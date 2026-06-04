"""FastMCP server exposing understand, generate, config, help tools."""

from __future__ import annotations

import asyncio
import os
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal, cast

import platformdirs
from fastmcp import FastMCP
from loguru import logger
from mcp_core.relay.tool_helpers import register_open_relay_tool

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
    from imagine_mcp import __version__

    return __version__


def _creds_state() -> str:
    # Read from os.environ -- settings singleton is frozen at import time
    # and does not observe post-startup relay-saved credentials.
    if any(
        os.environ.get(k) for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY")
    ):
        return "configured (env)"
    return "pending (run config tool)"


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
            settings.default_provider = cast(
                Literal["gemini", "openai", "grok"], value
            )
        case "default_tier":
            settings.default_tier = cast(Literal["poor", "rich"], value)
        case "cache_ttl_seconds":
            try:
                settings.cache_ttl_seconds = int(value)
            except ValueError:
                return {"status": "error", "message": "Value must be an integer."}
    return {"status": "ok", "key": key, "value": value}


def build_app() -> FastMCP:
    """Initialize the MCP application with all tools registered."""
    app = FastMCP("imagine-mcp", version=_get_version())

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


def main() -> None:
    """Entry point for the MCP server."""
    app = build_app()
    app.run()


if __name__ == "__main__":
    main()
