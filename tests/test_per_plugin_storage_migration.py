"""Verify migration to PerPluginStore + cred persistence works.

These tests validate HTTP-mode credential storage semantics. Stdio mode
forbids PerPluginStore reads (spec 2026-05-01 §4.1) -- see
``test_credential_state_stdio_no_fallback.py`` for the stdio-side guard.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _force_http_mode(monkeypatch):
    """Run all tests in this module under HTTP mode.

    ``credential_state.load_credentials`` / ``read_for_sub`` skip the
    PerPluginStore in stdio mode per spec 2026-05-01 §4.1, so the legacy
    storage tests must opt in to HTTP mode explicitly.
    """
    monkeypatch.setenv("MCP_TRANSPORT", "http")


def test_loads_from_new_path(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    from mcp_core.storage.per_plugin_store import PerPluginStore

    PerPluginStore("imagine").save({"GEMINI_API_KEY": "fake-key"})
    from imagine_mcp.credential_state import load_credentials

    assert load_credentials().get("GEMINI_API_KEY") == "fake-key"


def test_save_writes_to_new_path(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    from imagine_mcp.credential_state import save_credentials

    monkeypatch.delenv("PUBLIC_URL", raising=False)
    save_credentials({"GEMINI_API_KEY": "saved-key"})
    from mcp_core.storage.per_plugin_store import PerPluginStore

    assert PerPluginStore("imagine").load().get("GEMINI_API_KEY") == "saved-key"


def test_clear_removes_new_path(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    from imagine_mcp.credential_state import clear_credentials, save_credentials

    monkeypatch.delenv("PUBLIC_URL", raising=False)
    save_credentials({"x": "y"})
    clear_credentials()
    from mcp_core.storage.per_plugin_store import PerPluginStore

    assert PerPluginStore("imagine").load() is None


def test_per_sub_store_and_read(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-secret-value")
    from imagine_mcp.credential_state import read_for_sub, store_for_sub

    store_for_sub("user-abc", {"OPENAI_API_KEY": "sk-test"})
    assert read_for_sub("user-abc").get("OPENAI_API_KEY") == "sk-test"


def test_sub_isolation(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-secret-value")
    from imagine_mcp.credential_state import read_for_sub, store_for_sub

    store_for_sub("user-1", {"XAI_API_KEY": "key-1"})
    store_for_sub("user-2", {"XAI_API_KEY": "key-2"})
    assert read_for_sub("user-1").get("XAI_API_KEY") == "key-1"
    assert read_for_sub("user-2").get("XAI_API_KEY") == "key-2"


def test_relay_setup_load_config_from_file(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    from mcp_core.storage.per_plugin_store import PerPluginStore

    PerPluginStore("imagine").save({"GEMINI_API_KEY": "relay-key"})
    # Need to reload after monkeypatching home
    import importlib

    import imagine_mcp.relay_setup as rs

    importlib.reload(rs)
    result = rs.load_config_from_file()
    assert result is not None
    assert result.get("GEMINI_API_KEY") == "relay-key"


def test_relay_setup_reset_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    from mcp_core.storage.per_plugin_store import PerPluginStore

    PerPluginStore("imagine").save({"GEMINI_API_KEY": "to-delete"})
    import importlib

    import imagine_mcp.relay_setup as rs

    importlib.reload(rs)
    result = rs.reset_credentials()
    assert result["status"] == "reset"
    assert PerPluginStore("imagine").load() is None


def test_relay_setup_reset_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    import importlib

    import imagine_mcp.relay_setup as rs

    importlib.reload(rs)
    result = rs.reset_credentials()
    assert result["status"] == "not_found"


def test_relay_setup_reset_error(monkeypatch):
    import imagine_mcp.relay_setup as rs
    def mock_init(*args, **kwargs):
        raise Exception("forced failure")

    monkeypatch.setattr(rs, "PerPluginStore", mock_init)
    result = rs.reset_credentials()
    assert result["status"] == "error"
    assert result["error"] == "forced failure"
