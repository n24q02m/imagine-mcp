from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal, cast

import platformdirs
from loguru import logger
from mcp.server import Server
from mcp_core.app import BearerMCPApp

from imagine_mcp.config import settings
from imagine_mcp.dispatcher import (
    GenerationOptions,
    dispatch_generate,
    dispatch_understand,
)
from imagine_mcp.relay_schema import RELAY_SCHEMA

VALID_HELP_TOPICS = {"understand", "generate", "config"}

_VALID_SET_KEYS = {
    "log_level",
    "default_provider",
    "default_tier",
    "cache_ttl_seconds",
}


def _get_version() -> str:
    try:
        return version("imagine-mcp")
    except Exception:
        return "0.0.0-dev"


def _providers_configured() -> list[str]:
    """Check env vars for configured providers (shallow check)."""
    from imagine_mcp.dispatcher import _DEFAULT_PROVIDER_PRIORITY

    return [p for env, p in _DEFAULT_PROVIDER_PRIORITY if os.environ.get(env)]


def _providers_configured_live() -> list[str]:
    """Check credentials_for_current_request for providers (deep check)."""
    from imagine_mcp.credential_state import credentials_for_current_request
    from imagine_mcp.dispatcher import _DEFAULT_PROVIDER_PRIORITY

    creds = credentials_for_current_request()
    return [p for env, p in _DEFAULT_PROVIDER_PRIORITY if creds.get(env)]


def _creds_state() -> str:
    """Return human-readable status of the credential store."""
    from imagine_mcp.credential_state import _current_sub

    if _current_sub.get():
        return "multi-user (per-sub config)"
    return "single-user (env/config.enc)"


def _set_runtime(key: str | None, value: str | None) -> dict[str, Any]:
    if not key or key not in _VALID_SET_KEYS:
        return {
            "status": "error",
            "message": f"Invalid key {key!r}. Valid: {sorted(_VALID_SET_KEYS)}",
        }
    if value is None:
        return {"status": "error", "message": "Value is required."}

    match key:
        case "log_level":
            settings.log_level = cast(
                Literal["DEBUG", "INFO", "WARNING", "ERROR"], value
            )
        case "default_provider":
            settings.default_provider = cast(Literal["gemini", "openai", "grok"], value)
        case "default_tier":
            settings.default_tier = cast(Literal["poor", "rich"], value)
        case "cache_ttl_seconds":
            try:
                settings.cache_ttl_seconds = int(value)
            except ValueError:
                return {"status": "error", "message": "Value must be an integer."}
    return {"status": "ok", "key": key, "value": value}


@asynccontextmanager
async def lifespan(server: Server) -> AsyncIterator[None]:
    yield


def build_app() -> BearerMCPApp:
    """Initialize the MCP application with all tools registered."""
    app = BearerMCPApp("imagine-mcp", version=_get_version())

    @app.tool()
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
        options = GenerationOptions(
            reference_image_url=reference_image_url,
            job_id=job_id,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
        )
        return dispatch_generate(media_type, prompt, provider, tier, options=options)

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
        doc_file = files("imagine_mcp.docs").joinpath(f"{topic}.md")
        return doc_file.read_text(encoding="utf-8")

    from mcp_core.app import register_open_relay_tool

    register_open_relay_tool(app, "imagine-mcp", os.environ.get("PUBLIC_URL"))

    return app


async def _per_request_sub_scope(claims: dict[str, Any], next_: Any) -> None:
    from imagine_mcp.credential_state import _current_sub, _request_creds

    token_sub = _current_sub.set(claims.get("sub"))
    token_creds = _request_creds.set(None)
    try:
        await next_()
    finally:
        _current_sub.reset(token_sub)
        _request_creds.reset(token_creds)


async def run_http(port: int = 0) -> None:
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
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8080"))
        mode_label = "http remote relay (multi-user)"
    else:
        host = "127.0.0.1"
        mode_label = "http local relay"

    app = build_app()
    logger.info("imagine-mcp {} starting ({})", _get_version(), mode_label)
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
    asyncio.run(run_http())


if __name__ == "__main__":
    main()
