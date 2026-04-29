"""FastMCP server exposing understand, generate, config, help tools."""

from __future__ import annotations

import asyncio
import os
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
    # Read from os.environ -- settings singleton is frozen at import time
    # and does not observe post-startup relay-saved credentials.
    if any(
        os.environ.get(k) for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY")
    ):
        return "CONFIGURED"
    return "NEEDS_SETUP"


def _providers_configured() -> list[str]:
    out: list[str] = []
    if os.environ.get("GEMINI_API_KEY"):
        out.append("gemini")
    if os.environ.get("OPENAI_API_KEY"):
        out.append("openai")
    if os.environ.get("XAI_API_KEY"):
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

    register_open_relay_tool(app, "imagine-mcp", RELAY_SCHEMA)

    return app


async def run_http(port: int = 0) -> None:
    """Unified HTTP daemon -- single-user (default) or multi-user remote.

    Default (``PUBLIC_URL`` unset):
        Local HTTP daemon on 127.0.0.1:<port> via mcp-core's
        ``run_local_server``. Credential form at ``/authorize`` writes
        keys to the encrypted ``config.enc`` (single-user, single config).

    Multi-user remote (``PUBLIC_URL`` set):
        Bind ``0.0.0.0:8080`` so the daemon is reachable behind a reverse
        proxy. Each authorize session carries a fresh ``sub`` UUID
        generated by ``mcp_core.auth.local_oauth_app``; LLM API keys are
        scoped per-sub in ``IMAGINE_DATA_DIR/subs/<sub>/config.json``.
        Refuses to start if ``MCP_DCR_SERVER_SECRET`` is missing -- DCR
        requires a server secret to mint per-user JWTs safely.
    """
    from mcp_core.transport.local_server import run_local_server

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
    await run_local_server(
        app,
        server_name="imagine-mcp",
        relay_schema=RELAY_SCHEMA,
        port=port,
        host=host,
        open_browser=not public_url,
        on_credentials_saved=save_credentials,
    )


def main() -> None:
    """Sync wrapper for the default ``http local relay`` mode.

    Kept as the public entry point so `python -m imagine_mcp` and the
    ``imagine-mcp`` console_script both resolve to the same thing.
    Mode dispatch (stdio / remote-relay / local-relay) lives in
    ``imagine_mcp.__main__``.
    """
    asyncio.run(run_http())


if __name__ == "__main__":
    main()
