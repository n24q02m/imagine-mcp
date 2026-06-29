"""Tests for server status tools and credential reporting."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from imagine_mcp.server import (
    _creds_state,
    _providers_configured,
    _providers_configured_live,
    build_app,
)


@pytest.fixture
def app():
    return build_app()


def test_creds_state(monkeypatch) -> None:
    # No keys
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    # Ensure _is_http is true or it won't check store/env properly in the refactored version if it's meant to be live
    # Actually _providers_configured_live calls credentials_for_current_request
    assert _creds_state() == "NEEDS_SETUP"

    # One key
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    # Reset cache
    from imagine_mcp.credential_state import _request_creds

    _request_creds.set(None)
    assert _creds_state() == "CONFIGURED"


def test_providers_configured(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("XAI_API_KEY", "test")

    res = _providers_configured()
    assert "openai" in res
    assert "grok" in res
    assert len(res) == 2


def test_providers_configured_live(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.setenv("MCP_TRANSPORT", "http")

    from imagine_mcp.credential_state import _request_creds

    _request_creds.set(None)

    with patch(
        "imagine_mcp.credential_state.PerPluginStore.load",
        return_value={"OPENAI_API_KEY": "test", "XAI_API_KEY": "test"},
    ):
        res = _providers_configured_live()
        assert "openai" in res
        assert "grok" in res
        assert len(res) == 2


@pytest.mark.anyio
async def test_config_status(app, monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    from imagine_mcp.credential_state import _request_creds

    _request_creds.set(None)

    result = await app.call_tool("config", {"action": "status"})
    res = json.loads(result.content[0].text)

    assert res["credentials_state"] == "CONFIGURED"
    assert "gemini" in res["providers_configured"]
