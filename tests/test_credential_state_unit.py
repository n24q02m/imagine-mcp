from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from imagine_mcp import credential_state
from imagine_mcp.credential_state import (
    CLOUD_KEYS,
    credentials_for_current_request,
    set_current_sub,
)


@pytest.fixture
def mock_read_for_sub(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(credential_state, "read_for_sub", mock)
    return mock


def test_credentials_no_sub_returns_filtered_environ(monkeypatch):
    """Single-user mode (no sub): returns only CLOUD_KEYS from os.environ."""
    # Reset state
    set_current_sub(None)

    # Mock environment
    monkeypatch.setenv("XAI_API_KEY", "xai-val")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-val")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-val")
    monkeypatch.setenv("OTHER_VAR", "ignored")

    # Also ensure some CLOUD_KEYS are missing to test filtering
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-val")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-val")

    creds = credentials_for_current_request()

    assert "XAI_API_KEY" not in creds
    assert creds["OPENAI_API_KEY"] == "openai-val"
    assert creds["GEMINI_API_KEY"] == "gemini-val"
    assert "OTHER_VAR" not in creds
    assert set(creds.keys()).issubset(set(CLOUD_KEYS))


def test_credentials_with_sub_calls_read_for_sub(mock_read_for_sub, monkeypatch):
    """Multi-user mode: returns results from read_for_sub, ignores os.environ."""
    # Reset state and set sub
    set_current_sub("user-123")

    # Mock read_for_sub return value
    expected_creds = {"XAI_API_KEY": "sub-key"}
    mock_read_for_sub.return_value = expected_creds

    # Mock environment to ensure it's ignored
    monkeypatch.setenv("XAI_API_KEY", "env-key")

    creds = credentials_for_current_request()

    assert creds == expected_creds
    mock_read_for_sub.assert_called_once_with("user-123")


def test_credentials_caching(mock_read_for_sub):
    """Verify that credentials are cached per request scope."""
    set_current_sub("user-abc")

    mock_read_for_sub.return_value = {"GEMINI_API_KEY": "cached-key"}

    # First call
    creds1 = credentials_for_current_request()
    # Second call
    creds2 = credentials_for_current_request()

    assert creds1 is creds2
    assert creds1 == {"GEMINI_API_KEY": "cached-key"}
    # read_for_sub should only be called once due to caching
    assert mock_read_for_sub.call_count == 1


def test_credentials_cache_reset_on_sub_change(mock_read_for_sub):
    """Verify that setting a new sub resets the cache."""
    mock_read_for_sub.side_effect = [{"XAI_API_KEY": "key-a"}, {"XAI_API_KEY": "key-b"}]

    set_current_sub("sub-a")
    creds_a = credentials_for_current_request()
    assert creds_a == {"XAI_API_KEY": "key-a"}

    set_current_sub("sub-b")
    creds_b = credentials_for_current_request()
    assert creds_b == {"XAI_API_KEY": "key-b"}

    assert mock_read_for_sub.call_count == 2
