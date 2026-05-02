"""Regression: stdio mode MUST NOT read PerPluginStore as fallback.

Spec: ``.superpower/mcp-core/specs/2026-05-01-stdio-pure-http-multiuser.md``
§4.1 -- "Cred source: env vars ONLY (per OQ3, no auto-spawn relay)".

Before this guard, ``credential_state.load_credentials`` and
``read_for_sub`` would silently surface keys written by a previous
HTTP-mode session even when the current process runs in pure stdio
mode (no ``--http`` flag, ``MCP_TRANSPORT``/``TRANSPORT_MODE`` unset).
That broke the env-only invariant and could leak credentials across
storage scopes.
"""

from __future__ import annotations

import pytest

from imagine_mcp.credential_state import (
    PLUGIN_NAME,
    load_credentials,
    read_for_sub,
)


@pytest.fixture
def _no_http_env(monkeypatch):
    """Force stdio mode: clear all HTTP indicators."""
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.delenv("TRANSPORT_MODE", raising=False)
    monkeypatch.setattr("sys.argv", ["imagine-mcp"])


@pytest.fixture
def _http_env(monkeypatch):
    """Force HTTP mode via MCP_TRANSPORT env var."""
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.delenv("TRANSPORT_MODE", raising=False)
    monkeypatch.setattr("sys.argv", ["imagine-mcp"])


def test_stdio_skips_per_plugin_store_load(tmp_path, monkeypatch, _no_http_env):
    """Stdio mode: load_credentials returns {} even when store has keys."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    from mcp_core.storage.per_plugin_store import PerPluginStore

    # Simulate prior HTTP-mode write.
    PerPluginStore(PLUGIN_NAME).save({"GEMINI_API_KEY": "leaked-key"})

    # Stdio process must NOT see those keys.
    assert load_credentials() == {}


def test_stdio_skips_read_for_sub(tmp_path, monkeypatch, _no_http_env):
    """Stdio mode: read_for_sub returns {} even when sub bucket has keys."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-secret-value")
    from mcp_core.storage.per_plugin_store import PerPluginStore

    PerPluginStore(PLUGIN_NAME, "user-abc").save({"OPENAI_API_KEY": "sk-leaked"})

    assert read_for_sub("user-abc") == {}


def test_stdio_argv_http_flag_enables_per_plugin_store(tmp_path, monkeypatch):
    """``--http`` flag in argv enables HTTP-mode PerPluginStore reads."""
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.delenv("TRANSPORT_MODE", raising=False)
    monkeypatch.setattr("sys.argv", ["imagine-mcp", "--http"])
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    from mcp_core.storage.per_plugin_store import PerPluginStore

    PerPluginStore(PLUGIN_NAME).save({"GEMINI_API_KEY": "http-key"})

    assert load_credentials().get("GEMINI_API_KEY") == "http-key"


def test_http_mode_uses_per_plugin_store(tmp_path, monkeypatch, _http_env):
    """HTTP mode (MCP_TRANSPORT=http): load_credentials reads the store."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    from mcp_core.storage.per_plugin_store import PerPluginStore

    PerPluginStore(PLUGIN_NAME).save({"XAI_API_KEY": "xai-key"})

    result = load_credentials()
    assert result.get("XAI_API_KEY") == "xai-key"


def test_http_mode_uses_per_sub_store(tmp_path, monkeypatch, _http_env):
    """HTTP mode: read_for_sub returns the sub-scoped credentials."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-secret-value")
    from mcp_core.storage.per_plugin_store import PerPluginStore

    PerPluginStore(PLUGIN_NAME, "user-xyz").save({"OPENAI_API_KEY": "sk-xyz"})

    assert read_for_sub("user-xyz").get("OPENAI_API_KEY") == "sk-xyz"


def test_transport_mode_env_enables_per_plugin_store(tmp_path, monkeypatch):
    """``TRANSPORT_MODE=http`` env var also enables PerPluginStore reads."""
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.setenv("TRANSPORT_MODE", "http")
    monkeypatch.setattr("sys.argv", ["imagine-mcp"])
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    from mcp_core.storage.per_plugin_store import PerPluginStore

    PerPluginStore(PLUGIN_NAME).save({"GEMINI_API_KEY": "transport-key"})

    assert load_credentials().get("GEMINI_API_KEY") == "transport-key"
