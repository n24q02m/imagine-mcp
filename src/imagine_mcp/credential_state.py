"""Per-sub credential storage for multi-user remote mode + sub-aware save.

Migrated to mcp_core.storage.per_plugin_store for trust model alignment.
Storage layout:
    Single-user: ~/.imagine-mcp/config.json
    Multi-user:  ~/.imagine-mcp/subs/<sub>/config.json

Replaces legacy mcp_core.storage.config_file (shared config.enc) which
caused multi-daemon path-drift contention.

Stdio mode pure-env policy (spec 2026-05-01-stdio-pure-http-multiuser §4.1):
    Stdio = env vars ONLY. PerPluginStore reads are gated behind ``_is_http()``
    so that a stdio process never silently picks up credentials from a config
    file written by a previous HTTP-mode session. ``_is_http`` mirrors the
    detection logic in ``imagine_mcp.__main__`` (``--http`` flag,
    ``MCP_TRANSPORT=http``, ``TRANSPORT_MODE=http``).

Per-request sub contextvar (HTTP multi-user mode):
    The ``auth_scope`` middleware wired by ``imagine_mcp.server.run_http``
    sets ``_current_sub`` to the JWT ``sub`` claim for the duration of each
    MCP request. Tool handlers (``understand`` / ``generate``) and the
    dispatcher resolve credentials via ``credentials_for_current_request()``
    which picks the per-sub config when a sub is set, or merges os.environ
    when running single-user / stdio.
"""

from __future__ import annotations

import contextvars
import os
import sys

from mcp_core.storage.per_plugin_store import PerPluginStore

from imagine_mcp.config import PROVIDER_TO_KEY

PLUGIN_NAME = "imagine"

# Cloud provider API keys; derived from config.PROVIDER_TO_KEY.
CLOUD_KEYS: tuple[str, ...] = tuple(PROVIDER_TO_KEY.values())

# Per-request JWT sub. Set by ``auth_scope`` middleware in HTTP multi-user
# mode; ``None`` in stdio + single-user HTTP. ContextVar is asyncio-safe and
# stays scoped to the request task (ASGI handlers are tasks).
_current_sub: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "imagine_current_sub", default=None
)

# Request-scoped cache for resolved credentials to avoid repeated disk reads,
# decryption, and JSON parsing during a single tool execution.
_request_creds: contextvars.ContextVar[dict[str, str] | None] = contextvars.ContextVar(
    "imagine_request_creds", default=None
)


def set_current_sub(sub: str | None) -> None:
    """Set the JWT sub for the current request scope (testing helper).

    Production code should use ``_current_sub.set()`` directly inside the
    ``auth_scope`` callback so the matching ``reset(token)`` runs in a
    ``finally`` block.
    """
    _current_sub.set(sub)
    _request_creds.set(None)


def get_current_sub() -> str | None:
    """Return the JWT sub for the current request scope, or ``None``."""
    return _current_sub.get()


def credentials_for_current_request() -> dict[str, str]:
    """Resolve cloud-provider credentials for the active request.

    Resolution rules:

    * Multi-user HTTP (``_current_sub`` set): return the per-sub config from
      ``~/.imagine-mcp/subs/<sub>/config.json``. ``os.environ`` is NOT
      merged -- per-sub isolation is the whole point.
    * Single-user / stdio (no sub): return cloud keys from ``os.environ``
      so tool handlers see the same view as the legacy direct-env path.

    Returns a dict mapping ``CLOUD_KEYS`` -> value. Missing/empty keys are
    omitted so callers can use ``mapping.get(K)`` safely.
    """
    cached = _request_creds.get()
    if cached is not None:
        return cached

    sub = _current_sub.get()
    if sub is None:
        # Performance optimization:
        # Avoid O(N) iteration over os.environ.items() by iterating directly
        # over the bounded O(1) CLOUD_KEYS. This reduces latency significantly
        # when the environment has many variables.
        res = {k: v for k in CLOUD_KEYS if (v := os.environ.get(k))}
    else:
        res = read_for_sub(sub)

    _request_creds.set(res)
    return res


def _is_http() -> bool:
    """Return True when the current process runs in HTTP mode.

    Mirrors ``imagine_mcp.__main__.main`` so PerPluginStore fallback reads
    only happen in HTTP mode. In stdio mode, credentials must come from
    env vars exclusively (per spec 2026-05-01 §4.1 + OQ3).
    """
    return (
        "--http" in sys.argv
        or os.environ.get("MCP_TRANSPORT") == "http"
        or os.environ.get("TRANSPORT_MODE") == "http"
    )


# ---------------------------------------------------------------------------
# Low-level per-sub helpers (preserve existing API surface for server.py)
# ---------------------------------------------------------------------------


def store_for_sub(sub: str, config: dict[str, str]) -> None:
    """Persist ``config`` for a specific JWT subject."""
    PerPluginStore(PLUGIN_NAME, sub).save(config)


def read_for_sub(sub: str) -> dict[str, str]:
    """Read the stored config for ``sub``; ``{}`` if not yet stored.

    Per-sub reads only make sense in HTTP multi-user mode -- the JWT subject
    is issued by mcp-core's local OAuth AS, which only runs under
    ``run_http_server``. Returns ``{}`` in stdio mode (no fallback).
    """
    if not _is_http():
        return {}
    return PerPluginStore(PLUGIN_NAME, sub).load() or {}


# ---------------------------------------------------------------------------
# Public helpers (used by relay_setup + server)
# ---------------------------------------------------------------------------


def load_credentials(sub: str | None = None) -> dict:
    """Load credentials for optional sub. Returns {} if not found.

    Stdio mode skips PerPluginStore entirely (env-only policy); HTTP mode
    reads the per-sub or single-user store as before.
    """
    if not _is_http():
        return {}
    return PerPluginStore(PLUGIN_NAME, sub).load() or {}


def clear_credentials(sub: str | None = None) -> None:
    """Remove stored credentials for optional sub."""
    PerPluginStore(PLUGIN_NAME, sub).clear()


def save_credentials(
    config: dict[str, str],
    context: dict[str, str] | None = None,
) -> dict | None:
    """Sub-aware credentials persistence. Wired into ``run_http_server``.

    Multi-user remote mode (``PUBLIC_URL`` set):
        Every authorize session has a fresh ``sub`` UUID generated by
        ``mcp_core.auth.local_oauth_app``. We require it and scope the
        config under ``~/.imagine-mcp/subs/<sub>/config.json`` -- never
        write to a shared store (would leak credentials across users).

    Single-user default mode:
        Persist under ``~/.imagine-mcp/config.json`` and apply env vars.
    """
    if os.environ.get("PUBLIC_URL"):
        sub = context.get("sub") if context else None
        if not sub:
            raise RuntimeError("multi-user mode: SubjectContext sub required")
        store_for_sub(sub, config)
        return None

    # Single-user path: persist via PerPluginStore + apply env vars.
    PerPluginStore(PLUGIN_NAME).save(config)
    from imagine_mcp.relay_setup import apply_config

    apply_config(config)
    return None
