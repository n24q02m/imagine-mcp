from __future__ import annotations

import pytest

from imagine_mcp.credential_state import (
    CLOUD_KEYS,
    _request_creds,
    clear_credentials,
    credentials_for_current_request,
    get_current_sub,
    load_credentials,
    read_for_sub,
    save_credentials,
    set_current_sub,
    store_for_sub,
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


def test_credentials_with_sub_reads_store_mocked(monkeypatch):
    """Test both branches of credentials_for_current_request by mocking read_for_sub."""
    # Branch 1: sub is None
    set_current_sub(None)
    for k in CLOUD_KEYS:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("XAI_API_KEY", "xai-val")
    assert credentials_for_current_request() == {"XAI_API_KEY": "xai-val"}

    # Branch 2: sub is set
    set_current_sub("user-456")

    def mock_read(sub):
        assert sub == "user-456"
        return {"MOCK_KEY": "MOCK_VAL"}

    monkeypatch.setattr("imagine_mcp.credential_state.read_for_sub", mock_read)

    # Must clear cache first because set_current_sub does it, but we already set it
    # Actually set_current_sub("user-456") already cleared it.
    assert credentials_for_current_request() == {"MOCK_KEY": "MOCK_VAL"}


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


def test_get_current_sub():
    """Test get_current_sub returns the value from contextvar."""
    set_current_sub("test-sub-456")
    assert get_current_sub() == "test-sub-456"
    set_current_sub(None)
    assert get_current_sub() is None


def test_read_for_sub_stdio(monkeypatch):
    """read_for_sub returns {} in stdio mode."""
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.delenv("TRANSPORT_MODE", raising=False)
    monkeypatch.setattr("sys.argv", ["imagine-mcp"])
    assert read_for_sub("any-sub") == {}


def test_load_credentials_stdio(monkeypatch):
    """load_credentials returns {} in stdio mode."""
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.delenv("TRANSPORT_MODE", raising=False)
    monkeypatch.setattr("sys.argv", ["imagine-mcp"])
    assert load_credentials() == {}


def test_store_for_sub(tmp_path, monkeypatch):
    """store_for_sub persists config for a sub."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-secret")

    store_for_sub("user-999", {"XAI_API_KEY": "xai-val"})
    assert read_for_sub("user-999") == {"XAI_API_KEY": "xai-val"}


def test_clear_credentials(tmp_path, monkeypatch):
    """clear_credentials removes stored config."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-secret")

    store_for_sub("user-888", {"GEMINI_API_KEY": "g-val"})
    clear_credentials("user-888")
    assert read_for_sub("user-888") == {}


def test_save_credentials_multiuser(tmp_path, monkeypatch):
    """save_credentials in multi-user mode (PUBLIC_URL set)."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.setenv("PUBLIC_URL", "https://imagine.example.com")
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-secret")

    save_credentials({"API_KEY": "secret"}, context={"sub": "user-uuid"})
    assert read_for_sub("user-uuid") == {"API_KEY": "secret"}


def test_save_credentials_multiuser_no_sub(monkeypatch):
    """save_credentials raises error if sub is missing in multi-user mode."""
    monkeypatch.setenv("PUBLIC_URL", "https://imagine.example.com")
    with pytest.raises(
        RuntimeError, match="multi-user mode: SubjectContext sub required"
    ):
        save_credentials({"API_KEY": "secret"}, context={})
    with pytest.raises(
        RuntimeError, match="multi-user mode: SubjectContext sub required"
    ):
        save_credentials({"API_KEY": "secret"}, context=None)


def test_save_credentials_single_user(tmp_path, monkeypatch):
    """save_credentials in single-user mode."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.delenv("PUBLIC_URL", raising=False)

    # Mock apply_config to avoid side effects
    mock_called = False

    def mock_apply_config(config):
        nonlocal mock_called
        mock_called = True
        assert config == {"SINGLE_USER_KEY": "val"}

    monkeypatch.setattr("imagine_mcp.relay_setup.apply_config", mock_apply_config)

    save_credentials({"SINGLE_USER_KEY": "val"})
    assert load_credentials() == {"SINGLE_USER_KEY": "val"}
    assert mock_called is True
