"""FastMCP server exposing understand, generate, config, help tools."""

from __future__ import annotations

import asyncio
import ipaddress
import os
import re
from functools import cache, wraps
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import platformdirs
from fastmcp import FastMCP
from loguru import logger
from mcp.types import ToolAnnotations
from mcp_core.relay.tool_helpers import register_open_relay_tool

from imagine_mcp.config import settings
from imagine_mcp.dispatcher import dispatch_generate, dispatch_understand
from imagine_mcp.relay_schema import RELAY_SCHEMA
from imagine_mcp.security import build_external_tool_result

VALID_HELP_TOPICS = {"understand", "generate", "config"}

_VALID_SET_KEYS = {
    "log_level",
    "default_provider",
    "default_tier",
    "cache_ttl_seconds",
}


def _get_version() -> str:
    from imagine_mcp import __version__

    return __version__


def _creds_state() -> str:
    """Return CONFIGURED if any provider is set (env or store), else NEEDS_SETUP.

    Checks live store because env vars may not be populated at startup.
    """
    return "CONFIGURED" if _providers_configured_live() else "NEEDS_SETUP"


def _providers_configured() -> list[str]:
    """Return list of providers configured via environment variables."""
    from imagine_mcp.relay_setup import CREDENTIAL_KEYS

    _key_to_provider = {
        "GEMINI_API_KEY": "gemini",
        "OPENAI_API_KEY": "openai",
        "XAI_API_KEY": "grok",
        "GOOGLE_VERTEX_EXPRESS_API_KEY": "vertex_express",
    }
    out = []
    seen = set()
    for key in CREDENTIAL_KEYS:
        if (
            os.environ.get(key)
            and os.environ.get(key).strip()
            and (p := _key_to_provider.get(key, key)) not in seen
        ):
            seen.add(p)
            out.append(p)
    return out


def _providers_configured_live() -> list[str]:
    """Like _providers_configured but also checks PerPluginStore.

    env vars may not be populated at startup (no lifespan apply_config call),
    so this reads the store directly for an accurate live view.
    """
    from mcp_core.storage.per_plugin_store import PerPluginStore

    from imagine_mcp.relay_setup import CREDENTIAL_KEYS, PLUGIN_NAME

    saved = PerPluginStore(PLUGIN_NAME).load() or {}
    _key_to_provider = {
        "GEMINI_API_KEY": "gemini",
        "OPENAI_API_KEY": "openai",
        "XAI_API_KEY": "grok",
        "GOOGLE_VERTEX_EXPRESS_API_KEY": "vertex_express",
    }
    out = []
    seen = set()
    for key in CREDENTIAL_KEYS:
        if (
            (os.environ.get(key) and os.environ.get(key).strip())
            or (saved.get(key) and saved.get(key).strip())
        ) and (p := _key_to_provider.get(key, key)) not in seen:
            seen.add(p)
            out.append(p)
    return out


def _set_runtime(key: str | None, value: str | None) -> dict[str, Any]:
    if not key or key not in _VALID_SET_KEYS:
        return {
            "status": "error",
            "message": f"Invalid key. Valid: {sorted(_VALID_SET_KEYS)}",
        }
    return {
        "status": "ok",
        "message": f"Set {key}={value} (runtime only; persistent via mcp-core).",
    }


@cache
def _get_help_content(topic: str) -> str:
    """Read markdown documentation file from package resources."""
    doc_file = files("imagine_mcp.docs").joinpath(f"{topic}.md")
    return doc_file.read_text(encoding="utf-8")


def _wrap_tool(tool_name: str):
    """Decorate a tool so vision-model output derived from external media is
    XPIA-marked.

    The wrapped tool returns a plain ``dict``; this turns it into a
    ``fastmcp.tools.ToolResult`` so both response channels are defended: the
    text block gains ``<untrusted_{tool}_content>`` boundary tags and
    ``structured_content`` carries the envelope markers (a client reading
    structured output never sees the text block). FastMCP still derives the
    tool's ``outputSchema`` from the wrapped function's ``-> dict``
    annotation, which ``functools.wraps`` keeps reachable via
    ``__wrapped__``.

    Applied only to ``understand`` -- its ``text`` field is a vision model's
    reading of user-supplied ``media_urls``, so image/video-borne prompt
    injection can steer it. ``generate`` returns base64 media, not
    model-derived text, and does not need it.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):
            result = await func(*args, **kwargs)
            return build_external_tool_result(tool_name, result)

        return wrapper

    return decorator


def build_app() -> FastMCP:
    """Create FastMCP app with 4 tools registered."""
    app: FastMCP = FastMCP(
        "imagine",
        version=_get_version(),
        instructions=(
            "Image/video understanding and generation across Gemini, OpenAI, Grok. "
            "4 tools: understand, generate, config, help. "
            "Call help(topic='understand'|'generate'|'config') for detailed docs."
        ),
    )

    @app.tool(
        description=(
            "Understand images and/or videos (multi-URL) with a prompt. "
            "Gemini supports mixed image+video in one call; "
            "OpenAI/Grok are image-only."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    @_wrap_tool("understand")
    async def understand(
        media_urls: list[str],
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        tier: str = "poor",
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Understand image/video content with a prompt.

        ``model`` overrides the provider/tier catalog with a litellm
        'provider/model' string (e.g. 'gemini/gemini-3.1-pro-preview') --
        bypasses the provider/tier catalog.
        """
        if len(media_urls) > settings.max_media_urls:
            raise ValueError(
                f"Too many media_urls ({len(media_urls)}). "
                f"Max: {settings.max_media_urls}."
            )
        return await dispatch_understand(
            media_urls, prompt, provider, tier, max_tokens, model
        )

    @app.tool(
        description=(
            "Generate an image or video from a text prompt. "
            "Video is async: first call returns job_id; call again with job_id to poll."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        ),
    )
    async def generate(
        media_type: Literal["image", "video"],
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        tier: str = "poor",
        reference_image_url: str | None = None,
        job_id: str | None = None,
        output_mode: Literal["base64", "path", "both"] = "both",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
    ) -> dict[str, Any]:
        """Generate image or video.

        ``model`` overrides the provider/tier catalog with a litellm
        'provider/model' string -- bypasses the provider/tier catalog.
        """
        return await dispatch_generate(
            media_type,
            prompt,
            provider,
            tier,
            reference_image_url,
            job_id,
            aspect_ratio,
            duration_seconds,
            model,
            output_mode,
        )

    @app.tool(
        description=(
            "Server config + credential setup (MERGED). Actions: "
            "(setup) setup_status|setup_skip|setup_reset|setup_complete|warmup "
            "(relay_status|relay_skip|relay_reset|relay_complete honored as "
            "deprecated aliases); (runtime) status|set|cache_clear. "
            "Use the config__open_relay tool to open the credential form."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=False,
        ),
    )
    async def config(
        action: str,
        key: str | None = None,
        value: str | None = None,
    ) -> dict[str, Any]:
        """Server config and credential management."""
        from imagine_mcp import relay_setup

        match action:
            case "relay_status" | "setup_status":
                if action == "relay_status":
                    logger.warning(
                        "Deprecated action 'relay_status' honored; migrate to 'setup_status'."
                    )
                _live_providers = await asyncio.to_thread(_providers_configured_live)
                return {
                    "status": "configured" if _live_providers else "pending",
                    "providers_configured": _live_providers,
                }
            case "relay_complete" | "setup_complete":
                if action == "relay_complete":
                    logger.warning(
                        "Deprecated action 'relay_complete' honored; migrate to 'setup_complete'."
                    )
                _live_providers = await asyncio.to_thread(_providers_configured_live)
                return {
                    "status": "saved" if _live_providers else "no_credentials",
                    "providers_configured": _live_providers,
                }
            case "relay_skip" | "setup_skip":
                if action == "relay_skip":
                    logger.warning(
                        "Deprecated action 'relay_skip' honored; migrate to 'setup_skip'."
                    )
                _env_providers = await asyncio.to_thread(_providers_configured)
                if not _env_providers:
                    return {
                        "status": "needs_setup",
                        "message": "No env vars set. Call the config__open_relay tool to configure via browser.",
                    }
                return {
                    "status": "using_env",
                    "message": "Using env vars for credentials.",
                    "providers": _env_providers,
                }
            case "relay_reset" | "setup_reset":
                if action == "relay_reset":
                    logger.warning(
                        "Deprecated action 'relay_reset' honored; migrate to 'setup_reset'."
                    )
                return await asyncio.to_thread(relay_setup.reset_credentials)
            case "warmup":
                return {
                    "status": "ok",
                    "message": "No heavy resources to warm up in v1.",
                }
            case "status":
                return {
                    "version": await asyncio.to_thread(_get_version),
                    "credentials_state": await asyncio.to_thread(_creds_state),
                    "providers_configured": await asyncio.to_thread(
                        _providers_configured_live
                    ),
                    "default_provider": settings.default_provider,
                    "default_tier": settings.default_tier,
                    "cache_ttl_seconds": settings.cache_ttl_seconds,
                }
            case "set":
                return _set_runtime(key, value)
            case "cache_clear":
                from imagine_mcp.cache import ResponseCache

                cache_obj = ResponseCache(
                    path=Path(platformdirs.user_cache_dir("imagine-mcp")) / "cache",
                    default_ttl=settings.cache_ttl_seconds,
                )
                await asyncio.to_thread(cache_obj.clear)
                return {"status": "ok", "message": "Cache cleared."}
            case _:
                return {
                    "status": "error",
                    "message": (
                        f"Unknown action {action!r}. Valid: setup_status|"
                        "setup_skip|setup_reset|setup_complete|warmup|"
                        "status|set|cache_clear (call the config__open_relay "
                        "tool to open the credential form)"
                    ),
                }

    @app.tool(
        description=("Full documentation. Topics: understand | generate | config."),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    async def help(topic: str = "understand") -> str:
        """Load documentation for a specific tool or topic."""
        if topic not in VALID_HELP_TOPICS:
            return f"Unknown topic {topic!r}. Valid: {sorted(VALID_HELP_TOPICS)}"
        return await asyncio.to_thread(_get_help_content, topic)

    register_open_relay_tool(app, "imagine-mcp", os.environ.get("PUBLIC_URL"))

    return app


async def _per_request_sub_scope(claims: dict[str, Any], next_: Any) -> None:
    """``auth_scope`` middleware: pin JWT sub into a contextvar for the request."""
    from imagine_mcp.credential_state import _current_sub, _request_creds

    token_sub = _current_sub.set(claims.get("sub"))
    token_creds = _request_creds.set(None)
    try:
        await next_()
    finally:
        _current_sub.reset(token_sub)
        _request_creds.reset(token_creds)


async def run_http(port: int = 0) -> None:
    """Unified HTTP daemon -- single-user (default) or multi-user remote."""
    from mcp_core.transport.local_server import run_http_server

    from imagine_mcp.credential_state import save_credentials

    public_url = os.environ.get("PUBLIC_URL")
    if public_url:
        parsed = urlparse(public_url)
        if parsed.scheme.lower() not in ("http", "https"):
            raise SystemExit(
                f"imagine-mcp refuses to start: Invalid PUBLIC_URL scheme {parsed.scheme!r}. "
                "Only http/https are allowed."
            )
        if not parsed.hostname:
            raise SystemExit(
                "imagine-mcp refuses to start: Invalid PUBLIC_URL: missing hostname."
            )

        if not os.environ.get("MCP_DCR_SERVER_SECRET"):
            raise SystemExit(
                "imagine-mcp refuses to start: PUBLIC_URL set but "
                "MCP_DCR_SERVER_SECRET missing. Multi-user remote mode "
                "requires the DCR secret."
            )

        port_str = os.environ.get("MCP_PORT", "8080")
        try:
            port = int(port_str)
            if not 0 <= port <= 65535:
                raise ValueError()
        except ValueError:
            raise SystemExit(
                f"imagine-mcp refuses to start: Invalid MCP_PORT {port_str!r}."
            ) from None

        host_str = os.environ.get("MCP_HOST", "127.0.0.1")
        try:
            ipaddress.ip_address(host_str)
        except ValueError:
            if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host_str):
                raise SystemExit(
                    f"imagine-mcp refuses to start: Invalid MCP_HOST IP address {host_str!r}."
                ) from None
            if not re.match(
                r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$",
                host_str,
            ):
                raise SystemExit(
                    f"imagine-mcp refuses to start: Invalid MCP_HOST hostname {host_str!r}."
                ) from None

        host = host_str
        mode_label = "http remote relay (multi-user)"
    else:
        host = "127.0.0.1"
        mode_label = "http local relay"

    app = await asyncio.to_thread(build_app)
    _version_str = await asyncio.to_thread(_get_version)
    logger.info("imagine-mcp {} starting ({})", _version_str, mode_label)

    auth_disabled = os.environ.get("MCP_AUTH_DISABLE") == "1"
    await run_http_server(
        app,
        server_name="imagine-mcp",
        relay_schema=RELAY_SCHEMA,
        port=port,
        host=host,
        open_browser=not public_url,
        on_credentials_saved=save_credentials,
        auth_scope=_per_request_sub_scope if public_url else None,
        auth_disabled=auth_disabled,
    )


def main() -> None:
    """Sync wrapper for the HTTP mode entry point."""
    asyncio.run(run_http())


if __name__ == "__main__":
    main()
