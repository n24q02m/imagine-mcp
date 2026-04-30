"""G6 UX bug fixes — relay_status/relay_skip accuracy for imagine-mcp.

Bug 1: relay_status/relay_complete returned stale state (env-only check)
even when no env vars were populated at startup, because imagine-mcp
has no lifespan apply_config call.

Bug 2: relay_skip reported "Using env vars for credentials." even when
no env vars were actually set.

Fix: relay_status + relay_complete use _providers_configured_live() which
checks both os.environ AND PerPluginStore. relay_skip checks env vars
before claiming "using_env" and returns needs_setup if none are set.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest


def _relay_status() -> dict[str, Any]:
    """Simulate config(action='relay_status') using module-level helper."""
    from imagine_mcp.server import _providers_configured_live

    live = _providers_configured_live()
    return {
        "status": "configured" if live else "pending",
        "providers_configured": live,
    }


def _relay_skip() -> dict[str, Any]:
    """Simulate config(action='relay_skip') using module-level helper."""
    from imagine_mcp.server import _providers_configured

    env_providers = _providers_configured()
    if not env_providers:
        return {
            "status": "needs_setup",
            "message": "No env vars set. Run config(action='open_relay') to configure via browser.",
        }
    return {"status": "using_env", "providers": env_providers}


class TestRelayStatusLiveDerivedState:
    """relay_status derives state from live PerPluginStore, not env-only."""

    def test_returns_configured_when_store_has_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """relay_status returns configured when PerPluginStore has provider keys."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("XAI_API_KEY", raising=False)

        with patch(
            "mcp_core.storage.per_plugin_store.PerPluginStore.load",
            return_value={"GEMINI_API_KEY": "test-key-123"},
        ):
            result = _relay_status()

        assert result["status"] == "configured"
        assert "gemini" in result["providers_configured"]

    def test_returns_pending_when_store_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """relay_status returns pending when store empty and no env vars."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("XAI_API_KEY", raising=False)

        with patch(
            "mcp_core.storage.per_plugin_store.PerPluginStore.load",
            return_value={},
        ):
            result = _relay_status()

        assert result["status"] == "pending"
        assert result["providers_configured"] == []

    def test_response_includes_providers_configured_field(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """relay_status always includes providers_configured key in response."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("XAI_API_KEY", raising=False)

        with patch(
            "mcp_core.storage.per_plugin_store.PerPluginStore.load",
            return_value={},
        ):
            result = _relay_status()

        assert "providers_configured" in result
        assert isinstance(result["providers_configured"], list)

    def test_no_duplicate_providers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If same key appears in both env and store, provider appears only once."""
        monkeypatch.setenv("GEMINI_API_KEY", "key-from-env")

        with patch(
            "mcp_core.storage.per_plugin_store.PerPluginStore.load",
            return_value={"GEMINI_API_KEY": "key-from-store"},
        ):
            result = _relay_status()

        assert result["providers_configured"].count("gemini") == 1


class TestRelaySkipHonesty:
    """relay_skip reports needs_setup when no env vars are set (Bug 2 fix)."""

    def test_returns_needs_setup_when_no_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """relay_skip returns needs_setup status when no provider env vars set."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("XAI_API_KEY", raising=False)

        result = _relay_skip()

        assert result["status"] == "needs_setup"
        assert "open_relay" in result["message"]

    def test_returns_using_env_when_env_vars_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """relay_skip returns using_env status when provider env vars are set."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("XAI_API_KEY", raising=False)

        result = _relay_skip()

        assert result["status"] == "using_env"
        assert "openai" in result["providers"]
