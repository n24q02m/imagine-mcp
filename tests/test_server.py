from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastmcp import FastMCP

from imagine_mcp.server import (
    _creds_state,
    _get_version,
    _providers_configured,
    _providers_configured_live,
    _set_runtime,
    build_app,
)


def test_build_app_metadata():
    app = build_app()
    assert isinstance(app, FastMCP)
    assert app.name == "imagine"
    # Capture instructions to local variable to help type narrowing for 'ty'
    instructions = app.instructions
    assert instructions is not None
    assert "Image/video understanding and generation" in instructions
    assert "4 tools: understand, generate, config, help" in instructions


def test_get_version():
    from imagine_mcp import __version__

    assert _get_version() == __version__


def test_creds_state(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    assert _creds_state() == "NEEDS_SETUP"

    monkeypatch.setenv("GEMINI_API_KEY", "test")
    assert _creds_state() == "CONFIGURED"


def test_providers_configured(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    assert _providers_configured() == []

    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    assert sorted(_providers_configured()) == ["gemini", "openai"]


def test_set_runtime_logic():
    # Valid key
    res = _set_runtime("log_level", "DEBUG")
    assert res["status"] == "ok"
    assert "Set log_level=DEBUG" in res["message"]

    # Invalid key
    res = _set_runtime("invalid_key", "value")
    assert res["status"] == "error"
    assert "Invalid key" in res["message"]

    # None key
    res = _set_runtime(None, "value")
    assert res["status"] == "error"
    assert "Invalid key" in res["message"]


@patch("mcp_core.storage.per_plugin_store.PerPluginStore")
def test_providers_configured_live(mock_store_cls, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)

    mock_store = MagicMock()
    mock_store.load.return_value = {"OPENAI_API_KEY": "from_store"}
    mock_store_cls.return_value = mock_store

    # Should find openai from store
    assert _providers_configured_live() == ["openai"]

    # Should find gemini from env
    monkeypatch.setenv("GEMINI_API_KEY", "from_env")
    assert sorted(_providers_configured_live()) == ["gemini", "openai"]
