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

import json
from unittest.mock import patch

import pytest

from imagine_mcp.server import build_app


@pytest.fixture
def app():
    return build_app()


class TestRelayStatusLiveDerivedState:
    """relay_status derives state from live PerPluginStore, not env-only."""

    @pytest.mark.anyio
    async def test_returns_configured_when_store_has_keys(
        self, app, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """relay_status returns configured when PerPluginStore has provider keys."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("XAI_API_KEY", raising=False)

        with patch(
            "mcp_core.storage.per_plugin_store.PerPluginStore.load",
            return_value={"GEMINI_API_KEY": "test-key-123"},
        ):
            result = await app.call_tool("config", {"action": "relay_status"})
            res = json.loads(result.content[0].text)

        assert res["status"] == "configured"
        assert "gemini" in res["providers_configured"]

    @pytest.mark.anyio
    async def test_returns_pending_when_store_empty(
        self, app, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """relay_status returns pending when store empty and no env vars."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("XAI_API_KEY", raising=False)

        with patch(
            "mcp_core.storage.per_plugin_store.PerPluginStore.load",
            return_value={},
        ):
            result = await app.call_tool("config", {"action": "relay_status"})
            res = json.loads(result.content[0].text)

        assert res["status"] == "pending"
        assert res["providers_configured"] == []

    @pytest.mark.anyio
    async def test_response_includes_providers_configured_field(
        self, app, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """relay_status always includes providers_configured key in response."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("XAI_API_KEY", raising=False)

        with patch(
            "mcp_core.storage.per_plugin_store.PerPluginStore.load",
            return_value={},
        ):
            result = await app.call_tool("config", {"action": "relay_status"})
            res = json.loads(result.content[0].text)

        assert "providers_configured" in res
        assert isinstance(res["providers_configured"], list)

    @pytest.mark.anyio
    async def test_no_duplicate_providers(self, app, monkeypatch: pytest.MonkeyPatch) -> None:
        """If same key appears in both env and store, provider appears only once."""
        monkeypatch.setenv("GEMINI_API_KEY", "key-from-env")

        with patch(
            "mcp_core.storage.per_plugin_store.PerPluginStore.load",
            return_value={"GEMINI_API_KEY": "key-from-store"},
        ):
            result = await app.call_tool("config", {"action": "relay_status"})
            res = json.loads(result.content[0].text)

        assert res["providers_configured"].count("gemini") == 1


class TestRelaySkipHonesty:
    """relay_skip reports needs_setup when no env vars are set (Bug 2 fix)."""

    @pytest.mark.anyio
    async def test_returns_needs_setup_when_no_env_vars(
        self, app, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """relay_skip returns needs_setup status when no provider env vars set."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("XAI_API_KEY", raising=False)

        result = await app.call_tool("config", {"action": "relay_skip"})
        res = json.loads(result.content[0].text)

        assert res["status"] == "needs_setup"
        assert "open_relay" in res["message"]

    @pytest.mark.anyio
    async def test_returns_using_env_when_env_vars_set(
        self, app, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """relay_skip returns using_env status when provider env vars are set."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("XAI_API_KEY", raising=False)

        result = await app.call_tool("config", {"action": "relay_skip"})
        res = json.loads(result.content[0].text)

        assert res["status"] == "using_env"
        assert res["message"] == "Using env vars for credentials."
        assert "openai" in res["providers"]
