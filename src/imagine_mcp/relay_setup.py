"""Relay onboarding: resolve config via env -> config.enc -> browser form.

Wraps mcp_core.relay primitives. Follows wet-mcp / mnemo-mcp pattern.
"""

from __future__ import annotations

import os
import sys
from typing import Any

from loguru import logger

SERVER_NAME = "imagine-mcp"
CREDENTIAL_KEYS: list[str] = [
    "GOOGLE_AI_STUDIO_API_KEY",
    "OPENAI_API_KEY",
    "XAI_API_KEY",
]

# 5 minutes: user needs time to copy URL, open browser, fill up to 3 keys
RELAY_TIMEOUT_S = 300.0


def load_config_from_file() -> dict[str, str] | None:
    """Try to load config from encrypted config file. Returns None if not found."""
    try:
        from mcp_core.storage.config_file import read_config

        saved = read_config(SERVER_NAME)
        if saved and any(saved.get(k) for k in CREDENTIAL_KEYS):
            logger.info("Config loaded from file")
            return dict(saved)
        return None
    except Exception:
        return None


def apply_config(config: dict[str, str]) -> None:
    """Apply config dict to environment variables (does not overwrite existing)."""
    for key, value in config.items():
        if value and key not in os.environ:
            os.environ[key] = value
            logger.debug("Applied relay config: {}", key)


def save_credentials(
    config: dict[str, str],
    _context: dict[str, str] | None = None,
) -> dict | None:
    """Persist credentials from the OAuth form to config.enc + env vars.

    Wired into `run_local_server(on_credentials_saved=save_credentials)`.
    `_context` carries the per-authorize `sub` for future multi-user use;
    imagine-mcp is single-user by design so the subject is unused here.
    """
    from mcp_core.storage.config_file import write_config

    write_config(SERVER_NAME, config)
    apply_config(config)
    logger.info("Credentials saved via local OAuth form")
    return None


async def ensure_config(
    *, force: bool = False, timeout: float | None = RELAY_TIMEOUT_S
) -> dict[str, str] | None:
    """Resolve config: env vars -> config file -> relay setup -> degraded.

    Args:
        force: Skip env-var and config-file checks, go straight to relay.
        timeout: Relay poll timeout in seconds. None = no timeout (manual setup).

    Relay is ONLY triggered when steps 1-2 are ALL empty (unless ``force=True``).
    Returns config dict if resolved, None if skipped (degraded mode is OK).
    """
    if not force:
        if any(os.environ.get(k) for k in CREDENTIAL_KEYS):
            logger.info("Credentials found in environment, skipping relay")
            return None

        config = load_config_from_file()
        if config is not None:
            apply_config(config)
            return config

    # Remote-relay mode requires user-supplied URL (no centralized imagine.n24q02m.com)
    relay_url = os.environ.get("MCP_RELAY_URL")
    if not relay_url:
        logger.warning(
            "No credentials found and MCP_RELAY_URL not set; starting in degraded mode. "
            "Use `http local relay mode` (default) to set credentials via browser, "
            "or set env vars directly."
        )
        return None

    logger.info("Starting remote relay setup at %s", relay_url)
    try:
        from mcp_core.relay.client import create_session, poll_for_result

        from .relay_schema import RELAY_SCHEMA

        session = await create_session(relay_url, SERVER_NAME, RELAY_SCHEMA)  # ty: ignore[invalid-argument-type]

        timeout_msg = f", {int(timeout)}s timeout" if timeout else ""
        print(
            f"\nConfigure imagine-mcp providers (optional{timeout_msg}):"
            f"\n{session.relay_url}"
            f"\nSkip to run in degraded mode (tools return CredentialMissingError).\n",
            file=sys.stderr,
            flush=True,
        )

        config = await poll_for_result(relay_url, session, timeout_s=timeout)  # ty: ignore[invalid-argument-type]

        from mcp_core.storage.config_file import write_config

        write_config(SERVER_NAME, config)
        logger.info("Config saved to encrypted storage")

        apply_config(dict(config))
        return dict(config)

    except Exception as exc:
        logger.error("Relay setup failed: {}", exc)
        return None


def reset_credentials() -> dict[str, Any]:
    """Delete encrypted config. Next run will re-prompt via relay.

    Returns {"status": "reset"} on success, {"status": "not_found"} if no config.
    """
    try:
        from mcp_core.storage.config_file import delete_config

        delete_config(SERVER_NAME)
        return {"status": "reset", "server": SERVER_NAME}
    except FileNotFoundError:
        return {"status": "not_found", "server": SERVER_NAME}
    except Exception as exc:
        logger.error("reset_credentials failed: {}", exc)
        return {"status": "error", "error": str(exc)}
