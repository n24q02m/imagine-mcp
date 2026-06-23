from __future__ import annotations

import os
from unittest.mock import MagicMock

from imagine_mcp.credential_state import (
    clear_env_creds_cache,
    credentials_for_current_request,
    set_current_sub,
)
from imagine_mcp.relay_setup import apply_config


def test_env_creds_cache_efficiency(monkeypatch):
    """Verify that os.environ.get is only called during the first cache population."""
    set_current_sub(None)
    clear_env_creds_cache()

    # Mock os.environ.get to track calls
    original_get = os.environ.get
    mock_get = MagicMock(side_effect=original_get)
    monkeypatch.setattr(os.environ, "get", mock_get)

    # First call - should trigger O(K) calls to os.environ.get
    creds1 = credentials_for_current_request()
    initial_call_count = mock_get.call_count
    assert initial_call_count > 0

    # Reset mock call count
    mock_get.reset_mock()

    # Second call (same request) - should use _request_creds cache (0 calls)
    creds2 = credentials_for_current_request()
    assert mock_get.call_count == 0
    assert creds2 is creds1

    # Simulate new request by clearing _request_creds but keeping _env_creds_cache
    set_current_sub(None)

    # Third call (new request) - should use _env_creds_cache (0 calls)
    creds3 = credentials_for_current_request()
    assert mock_get.call_count == 0
    assert creds3 == creds1


def test_env_creds_cache_invalidation(monkeypatch):
    """Verify that apply_config invalidates the cache when environ changes."""
    set_current_sub(None)
    clear_env_creds_cache()

    monkeypatch.setenv("GEMINI_API_KEY", "old-key")

    # Populate cache
    creds1 = credentials_for_current_request()
    assert creds1.get("GEMINI_API_KEY") == "old-key"

    # Update via apply_config
    apply_config({"GEMINI_API_KEY": "new-key"})

    # Simulate new request
    set_current_sub(None)

    # Should see new key
    creds2 = credentials_for_current_request()
    assert creds2.get("GEMINI_API_KEY") == "new-key"


def test_apply_config_no_churn(monkeypatch):
    """Verify that apply_config does NOT invalidate cache if nothing changed."""
    set_current_sub(None)
    clear_env_creds_cache()

    monkeypatch.setenv("GEMINI_API_KEY", "same-key")

    # Populate cache
    credentials_for_current_request()

    # Mock clear_env_creds_cache to see if it's called
    import imagine_mcp.credential_state

    mock_clear = MagicMock()
    monkeypatch.setattr(
        imagine_mcp.credential_state, "clear_env_creds_cache", mock_clear
    )

    # Call apply_config with SAME value
    apply_config({"GEMINI_API_KEY": "same-key"})

    assert mock_clear.call_count == 0
