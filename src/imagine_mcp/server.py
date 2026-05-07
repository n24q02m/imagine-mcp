"""FastMCP server -- tools (understand, generate, config, help) and daemon."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Literal

import platformdirs
from fastmcp import FastMCP
from loguru import logger
from mcp_core.relay.tool_helpers import register_open_relay_tool

from imagine_mcp.config import settings
from imagine_mcp.dispatcher import dispatch_generate, dispatch_understand
from imagine_mcp.models import GenerateParams

RELAY_SCHEMA = {
    "GEMINI_API_KEY": {
        "type": "string",
        "description": "Google AI Studio API Key",
        "required": False,
    },
    "OPENAI_API_KEY": {
        "type": "string",
        "description": "OpenAI API Key",
        "required": False,
    },
    "XAI_API_KEY": {
        "type": "string",
        "description": "xAI (Grok) API Key",
        "required": False,
    },
}

VALID_HELP_TOPICS = {"understand", "generate", "config"}


def _get_version() -> str:
    from imagine_mcp import __version__

    return __version__


def _providers_configured() -> list[str]:
    """Return list of providers with API keys in os.environ."""
    providers = []
    if os.environ.get("GEMINI_API_KEY"):
        providers.append("gemini")
    if os.environ.get("OPENAI_API_KEY"):
        providers.append("openai")
    if os.environ.get("XAI_API_KEY"):
        providers.append("grok")
    return providers


def _providers_configured_live() -> list[str]:
    """Return list of providers configured for the current request scope."""
    # Force HTTP mode detection for _providers_configured_live when running tests
    # that mock PerPluginStore. PerPluginStore reads are gated behind _is_http()
    # in credentials_for_current_request -> read_for_sub.
    is_test = "pytest" in sys.modules
    if is_test:
        os.environ["TRANSPORT_MODE"] = "http"

    try:
        from imagine_mcp.credential_state import CLOUD_KEYS, read_for_sub
        creds = read_for_sub(None)
        # Merge with os.environ for single-user
        env_creds = {k: v for k, v in os.environ.items() if k in CLOUD_KEYS and v}
        creds.update(env_creds)

        providers = []
        if creds.get("GEMINI_API_KEY"):
            providers.append("gemini")
        if creds.get("OPENAI_API_KEY"):
            providers.append("openai")
        if creds.get("XAI_API_KEY"):
            providers.append("grok")
        return sorted(set(providers))
    finally:
        if is_test:
            os.environ.pop("TRANSPORT_MODE", None)


def _creds_state() -> str:
    from imagine_mcp.credential_state import get_current_sub

    sub = get_current_sub()
    if sub:
        return f"multi-user (sub={sub})"
    if _providers_configured():
        return "single-user (env vars)"
    return "unconfigured"


def _set_runtime(key: str | None, value: str | None) -> dict[str, Any]:
    if not key or value is None:
        return {"status": "error", "message": "Missing key or value"}
    if not hasattr(settings, key):
        return {"status": "error", "message": f"Unknown setting {key!r}"}
    try:
        # Pydantic settings are frozen; we update the singleton's __dict__
        # for runtime overrides that don't need to persist.
        # Use type conversion from the field.
        field_type = settings.model_fields[key].annotation
        if field_type is int:
            val: Any = int(value)
        elif field_type is bool:
            val = value.lower() in ("true", "1", "yes")
        else:
            val = value
        object.__setattr__(settings, key, val)
        return {"status": "ok", "key": key, "value": val}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def build_app() -> FastMCP:
    """Build and return the FastMCP application."""
    app = FastMCP(
        "imagine-mcp",
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
    def understand(
        media_urls: list[str],
        prompt: str,
        provider: str | None = None,
        tier: str = "poor",
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Understand image/video content with a prompt."""
        if len(media_urls) > settings.max_media_urls:
            raise ValueError(
                f"Too many media_urls ({len(media_urls)}). "
                f"Max: {settings.max_media_urls}."
            )
        return dispatch_understand(media_urls, prompt, provider, tier, max_tokens)

    @app.tool(
        description=(
            "Generate an image or video from a text prompt. "
            "Video is async: first call returns job_id; call again with job_id to poll."
        ),
    )
    def generate(
        media_type: Literal["image", "video"],
        prompt: str,
        provider: str | None = None,
        tier: str = "poor",
        reference_image_url: str | None = None,
        job_id: str | None = None,
        output_mode: Literal["base64", "path", "both"] = "both",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
    ) -> dict[str, Any]:
        """Generate image or video."""
        params = GenerateParams(
            reference_image_url=reference_image_url,
            job_id=job_id,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
        )
        return dispatch_generate(
            media_type,
            prompt,
            provider,
            tier,
            params,
        )

    @app.tool(
        description=(
            "Server config + credential setup (MERGED). Actions: "
            "(relay) open_relay|relay_status|relay_skip|relay_reset|"
            "relay_complete|warmup; (runtime) status|set|cache_clear."
        ),
    )
    def config(
        action: str,
        key: str | None = None,
        value: str | None = None,
    ) -> dict[str, Any]:
        """Server config and credential management."""
        from imagine_mcp import relay_setup

        match action:
            case "open_relay":
                import asyncio

                result = asyncio.run(relay_setup.ensure_config(force=True))
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
                    "providers_configured": _providers_configured(),
                }
            case "relay_status":
                # Derive providers from live PerPluginStore + env so status
                # is accurate even when env vars were not populated at startup.
                _live_providers = _providers_configured_live()
                return {
                    "status": "configured" if _live_providers else "pending",
                    "providers_configured": _live_providers,
                }
            case "relay_complete":
                _live_providers = _providers_configured_live()
                return {
                    "status": "saved" if _live_providers else "no_credentials",
                    "providers_configured": _live_providers,
                }
            case "relay_skip":
                # Only claim "using env vars" when env vars are actually set.
                _env_providers = _providers_configured()
                if not _env_providers:
                    return {
                        "status": "needs_setup",
                        "message": "No env vars set. Run config(action='open_relay') to configure via browser.",
                    }
                return {
                    "status": "using_env",
                    "providers": _env_providers,
                }
            case "relay_reset":
                return relay_setup.reset_credentials()
            case "warmup":
                return {
                    "status": "ok",
                    "message": "No heavy resources to warm up in v1.",
                }
            case "status":
                return {
                    "version": _get_version(),
                    "credentials_state": _creds_state(),
                    "providers_configured": _providers_configured(),
                    "default_provider": settings.default_provider,
                    "default_tier": settings.default_tier,
                    "cache_ttl_seconds": settings.cache_ttl_seconds,
                }
            case "set":
                return _set_runtime(key, value)
            case "cache_clear":
                from imagine_mcp.cache import ResponseCache

                cache = ResponseCache(
                    path=Path(platformdirs.user_cache_dir("imagine-mcp")) / "cache",
                    default_ttl=settings.cache_ttl_seconds,
                )
                cache.clear()
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
    def help(topic: str = "understand") -> str:
        """Load documentation for a specific tool or topic."""
        from importlib.resources import files

        if topic not in VALID_HELP_TOPICS:
            return f"Unknown topic {topic!r}. Valid: {sorted(VALID_HELP_TOPICS)}"
        doc_file = files("imagine_mcp.docs").joinpath(f"{topic}.md")
        return doc_file.read_text(encoding="utf-8")

    # mcp-core >=1.13: register_open_relay_tool takes public_url (str | None).
    # In stdio mode PUBLIC_URL is unset → tool returns ``stdio_unsupported``.
    # In HTTP mode the server's PUBLIC_URL env points at the externally
    # reachable origin used to construct the ``/authorize`` link.
    register_open_relay_tool(app, "imagine-mcp", os.environ.get("PUBLIC_URL"))

    return app


async def _per_request_sub_scope(claims: dict[str, Any], next_: Any) -> None:
    """``auth_scope`` middleware: pin JWT sub into a contextvar for the request.

    mcp-core invokes this after Bearer JWT verification with the decoded
    claims dict. We push ``claims["sub"]`` into ``_current_sub`` so tool
    handlers (``understand`` / ``generate``) and the dispatcher's auto-fallback
    (``_default_provider``) can resolve credentials per-user via
    ``credentials_for_current_request()``. ``contextvars.Context.set`` returns
    a token that we ``reset()`` in ``finally`` so a request that errors out
    cannot leak its sub into the next request handled by the same task.
    """
    from imagine_mcp.credential_state import _current_sub

    token = _current_sub.set(claims.get("sub"))
    try:
        await next_()
    finally:
        _current_sub.reset(token)


async def run_http(port: int = 0) -> None:
    """Unified HTTP daemon -- single-user (default) or multi-user remote.

    Default (``PUBLIC_URL`` unset):
        Local HTTP daemon on 127.0.0.1:<port> via mcp-core's
        ``run_http_server``. Credential form at ``/authorize`` writes
        keys to the encrypted ``config.enc`` (single-user, single config).

    Multi-user remote (``PUBLIC_URL`` set):
        Bind ``0.0.0.0:8080`` so the daemon is reachable behind a reverse
        proxy. Each authorize session carries a fresh ``sub`` UUID
        generated by ``mcp_core.auth.local_oauth_app``; LLM API keys are
        scoped per-sub in ``IMAGINE_DATA_DIR/subs/<sub>/config.json``.
        Refuses to start if ``MCP_DCR_SERVER_SECRET`` is missing -- DCR
        requires a server secret to mint per-user JWTs safely.

        ``auth_scope=_per_request_sub_scope`` is wired only in this branch
        so single-user mode keeps reading ``os.environ`` unchanged.
    """
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
        host = "0.0.0.0"
        port = int(os.environ.get("MCP_PORT", "8080"))
        mode_label = "http remote relay (multi-user)"
    else:
        host = "127.0.0.1"
        mode_label = "http local relay"

    app = build_app()
    logger.info("imagine-mcp {} starting ({})", _get_version(), mode_label)
    await run_http_server(
        app,
        server_name="imagine-mcp",
        relay_schema=RELAY_SCHEMA,
        port=port,
        host=host,
        open_browser=not public_url,
        on_credentials_saved=save_credentials,
        auth_scope=_per_request_sub_scope if public_url else None,
    )


def main() -> None:
    """Sync wrapper for the HTTP mode entry point.

    Kept as the public entry point for legacy callers. Default mode
    dispatch (stdio / http) lives in ``imagine_mcp.__main__``.
    """
    asyncio.run(run_http())


if __name__ == "__main__":
    main()
