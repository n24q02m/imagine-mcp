"""FastMCP server exposing understand, generate, config, help tools."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any, Literal

import platformdirs
from fastmcp import FastMCP
from loguru import logger

from imagine_mcp.config import settings
from imagine_mcp.dispatcher import dispatch_generate, dispatch_understand

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
    if (
        settings.google_ai_studio_api_key
        or settings.openai_api_key
        or settings.xai_api_key
    ):
        return "CONFIGURED"
    return "NEEDS_SETUP"


def _providers_configured() -> list[str]:
    out: list[str] = []
    if settings.google_ai_studio_api_key:
        out.append("gemini")
    if settings.openai_api_key:
        out.append("openai")
    if settings.xai_api_key:
        out.append("grok")
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


def build_app() -> FastMCP:
    """Create FastMCP app with 4 tools registered."""
    app: FastMCP = FastMCP(
        "imagine-mcp",
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
        provider: str = "gemini",
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
        provider: str = "gemini",
        tier: str = "poor",
        reference_image_url: str | None = None,
        job_id: str | None = None,
        output_mode: Literal["base64", "path", "both"] = "both",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
    ) -> dict[str, Any]:
        """Generate image or video."""
        return dispatch_generate(
            media_type,
            prompt,
            provider,
            tier,
            reference_image_url,
            job_id,
            aspect_ratio,
            duration_seconds,
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
                return {
                    "status": (
                        "configured" if _creds_state() == "CONFIGURED" else "pending"
                    ),
                    "providers_configured": _providers_configured(),
                }
            case "relay_complete":
                return {
                    "status": "saved"
                    if _creds_state() == "CONFIGURED"
                    else "no_credentials",
                    "providers_configured": _providers_configured(),
                }
            case "relay_skip":
                return {
                    "status": "skipped",
                    "message": "Using env vars for credentials.",
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

    return app


def main() -> None:
    """Default entry: http local relay mode via mcp-core."""
    app = build_app()
    logger.info("imagine-mcp {} starting", _get_version())

    try:
        from mcp_core.transport import run_local_server

        from imagine_mcp.relay_schema import RELAY_SCHEMA

        run_local_server(
            app,
            server_name="imagine-mcp",
            relay_schema=RELAY_SCHEMA,
            open_browser=True,
        )
    except ImportError:
        logger.warning("mcp_core not installed; falling back to FastMCP .run()")
        app.run()


if __name__ == "__main__":
    main()
