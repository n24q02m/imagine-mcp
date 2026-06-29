from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from imagine_mcp.credential_state import set_current_sub
from imagine_mcp.server import build_app


@pytest.fixture
def app():
    return build_app()


class TestMultiUserStatusAccuracy:
    """Tests for sub-aware status tools and isolation."""

    @pytest.mark.anyio
    async def test_relay_status_sub_aware(
        self, app, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """relay_status isolation: sub-1 has keys, global/sub-2 empty."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("XAI_API_KEY", raising=False)
        monkeypatch.setenv("MCP_TRANSPORT", "http")  # Enable _is_http()

        # Patch PerPluginStore where it is used in credential_state
        with patch("imagine_mcp.credential_state.PerPluginStore") as mock_store_cls:
            mock_sub1_store = MagicMock()
            mock_sub1_store.load.return_value = {"GEMINI_API_KEY": "key-sub1"}

            mock_global_store = MagicMock()
            mock_global_store.load.return_value = {}

            def get_store(name, sub=None):
                if sub == "sub-1":
                    return mock_sub1_store
                return mock_global_store

            mock_store_cls.side_effect = get_store

            # 1. No sub -> pending
            set_current_sub(None)
            result = await app.call_tool("config", {"action": "relay_status"})
            res = json.loads(result.content[0].text)
            assert res["status"] == "pending"

            # 2. sub-1 -> configured
            set_current_sub("sub-1")
            try:
                result = await app.call_tool("config", {"action": "relay_status"})
                res = json.loads(result.content[0].text)
                assert res["status"] == "configured"
                assert "gemini" in res["providers_configured"]
            finally:
                set_current_sub(None)

    @pytest.mark.anyio
    async def test_relay_skip_honesty_multiuser(
        self, app, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """relay_skip should NOT claim server env vars are for the user."""
        monkeypatch.setenv("GEMINI_API_KEY", "server-secret")

        # No sub -> uses env
        set_current_sub(None)
        result = await app.call_tool("config", {"action": "relay_skip"})
        res = json.loads(result.content[0].text)
        assert res["status"] == "using_env"

        # Sub set -> needs setup (ignoring server env)
        set_current_sub("user-123")
        try:
            result = await app.call_tool("config", {"action": "relay_skip"})
            res = json.loads(result.content[0].text)
            assert res["status"] == "needs_setup"
            assert "open_relay" in res["message"]
        finally:
            set_current_sub(None)

    @pytest.mark.anyio
    async def test_relay_reset_sub_aware(self, app) -> None:
        """relay_reset clears user-specific store, not global store."""
        with patch("imagine_mcp.relay_setup.PerPluginStore") as mock_store_cls:
            mock_user_store = MagicMock()
            mock_user_store.cred_path.exists.return_value = True

            mock_store_cls.return_value = mock_user_store

            set_current_sub("user-123")
            try:
                await app.call_tool("config", {"action": "relay_reset"})

                # Verify PerPluginStore was called with the user sub
                args, kwargs = mock_store_cls.call_args
                assert kwargs.get("sub") == "user-123" or (
                    len(args) > 1 and args[1] == "user-123"
                )
                mock_user_store.clear.assert_called_once()
            finally:
                set_current_sub(None)

    @pytest.mark.anyio
    async def test_single_user_http_live_merge(
        self, app, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Single-user HTTP merges env + store (Bug 1 fix)."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
        monkeypatch.setenv("MCP_TRANSPORT", "http")  # Enable _is_http()

        # Patch PerPluginStore in credential_state for single-user path
        with patch("imagine_mcp.credential_state.PerPluginStore") as mock_store_cls:
            mock_instance = MagicMock()
            mock_instance.load.return_value = {"GEMINI_API_KEY": "sk-store"}
            mock_store_cls.return_value = mock_instance

            result = await app.call_tool("config", {"action": "relay_status"})
            res = json.loads(result.content[0].text)

            assert res["status"] == "configured"
            assert "gemini" in res["providers_configured"]
            assert "openai" in res["providers_configured"]
