"""FastMCP server exposing understand, generate, config, help tools."""

from __future__ import annotations

import asyncio
import os
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal

import platformdirs
from fastmcp import FastMCP
from loguru import logger
from mcp_core.relay.tool_helpers import register_open_relay_tool

from imagine_mcp.config import settings
from imagine_mcp.dispatcher import dispatch_generate, dispatch_understand
from imagine_mcp.relay_schema import RELAY_SCHEMA

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
    }
    # ⚡ Bolt: Use list(dict.fromkeys(...)) with generator expression for faster order-preserving deduplication
    # Expected impact: Reduces Python loop overhead by delegating deduplication to native C dict implementation
    return list(
        dict.fromkeys(
            _key_to_provider.get(key, key)
            for key in CREDENTIAL_KEYS
            if os.environ.get(key)
        )
    )


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
    }
    # ⚡ Bolt: Use list(dict.fromkeys(...)) with generator expression for faster order-preserving deduplication
    # Expected impact: Reduces Python loop overhead by delegating deduplication to native C dict implementation
    return list(
        dict.fromkeys(
            _key_to_provider.get(key, key)
            for key in CREDENTIAL_KEYS
            if os.environ.get(key) or saved.get(key)
        )
    )


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
    )
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
            "(relay) open_relay|relay_status|relay_skip|relay_reset|"
            "relay_complete|warmup; (runtime) status|set|cache_clear."
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
            case "open_relay":
                result = await relay_setup.ensure_config(force=True)
                if result is None:
                    return {
                        "status": "degraded",
                        "message": (
                            "No credentials loaded. Set MCP_RELAY_URL and retry, "
                            "or run the server in `http local relay mode` (default)."
                        ),
                    }
                return {
                    "status": "saved",
                    "providers_configured": await asyncio.to_thread(
                        _providers_configured_live
                    ),
                }
            case "relay_status":
                _live_providers = await asyncio.to_thread(_providers_configured_live)
                return {
                    "status": "configured" if _live_providers else "pending",
                    "providers_configured": _live_providers,
                }
            case "relay_complete":
                _live_providers = await asyncio.to_thread(_providers_configured_live)
                return {
                    "status": "saved" if _live_providers else "no_credentials",
                    "providers_configured": _live_providers,
                }
            case "relay_skip":
                _env_providers = await asyncio.to_thread(_providers_configured)
                if not _env_providers:
                    return {
                        "status": "needs_setup",
                        "message": "No env vars set. Run config(action='open_relay') to configure via browser.",
                    }
                return {
                    "status": "using_env",
                    "message": "Using env vars for credentials.",
                    "providers": _env_providers,
                }
            case "relay_reset":
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
                        f"Unknown action {action!r}. Valid: open_relay|relay_status|"
                        "relay_skip|relay_reset|relay_complete|warmup|"
                        "status|set|cache_clear"
                    ),
                }

    @app.tool(
        description=("Full documentation. Topics: understand | generate | config."),
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
        if not os.environ.get("MCP_DCR_SERVER_SECRET"):
            raise SystemExit(
                "imagine-mcp refuses to start: PUBLIC_URL set but "
                "MCP_DCR_SERVER_SECRET missing. Multi-user remote mode "
                "requires the DCR secret."
            )
        host = os.environ.get("MCP_HOST", "127.0.0.1")
        port = int(os.environ.get("MCP_PORT", "8080"))
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
