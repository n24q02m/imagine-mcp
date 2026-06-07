from __future__ import annotations

from imagine_mcp.credential_state import (
    CLOUD_KEYS,
    _request_creds,
    credentials_for_current_request,
    set_current_sub,
)


def test_credentials_no_sub_reads_environ(monkeypatch):
    """When no sub is set, it reads from os.environ for CLOUD_KEYS."""
    set_current_sub(None)

    # Clear relevant env vars
    for k in CLOUD_KEYS:
        monkeypatch.delenv(k, raising=False)

    monkeypatch.setenv("GEMINI_API_KEY", "gemini-val")
    monkeypatch.setenv("OTHER_VAR", "ignored")

    creds = credentials_for_current_request()
    assert creds == {"GEMINI_API_KEY": "gemini-val"}
    assert "OTHER_VAR" not in creds


def test_credentials_with_sub_reads_store(tmp_path, monkeypatch):
    """When sub is set, it reads from PerPluginStore (via read_for_sub)."""
    # Force HTTP mode so read_for_sub works
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-secret-value")
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    from mcp_core.storage.per_plugin_store import PerPluginStore

    from imagine_mcp.credential_state import PLUGIN_NAME

    sub_id = "user-123"
    set_current_sub(sub_id)

    # Save some creds for this sub
    PerPluginStore(PLUGIN_NAME, sub_id).save({"OPENAI_API_KEY": "sk-123"})

    # Set different creds in environ - they should be IGNORED
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")

    creds = credentials_for_current_request()
    assert creds == {"OPENAI_API_KEY": "sk-123"}


def test_credentials_caching(monkeypatch):
    """Test that results are cached in _request_creds."""
    set_current_sub(None)
    monkeypatch.setenv("GEMINI_API_KEY", "val1")

    # First call caches val1
    creds1 = credentials_for_current_request()
    assert creds1 == {"GEMINI_API_KEY": "val1"}

    # Change environment
    monkeypatch.setenv("GEMINI_API_KEY", "val2")

    # Second call should still return val1 from cache
    creds2 = credentials_for_current_request()
    assert creds2 == {"GEMINI_API_KEY": "val1"}


def test_set_current_sub_clears_cache(monkeypatch):
    """Test that set_current_sub clears the cache."""
    set_current_sub(None)
    monkeypatch.setenv("GEMINI_API_KEY", "val1")

    credentials_for_current_request()
    assert _request_creds.get() is not None

    # Changing sub should clear cache
    set_current_sub("new-sub")
    assert _request_creds.get() is None

    # Also verify it clears when setting back to None
    _request_creds.set({"dummy": "data"})
    set_current_sub(None)
    assert _request_creds.get() is None
