from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from imagine_mcp import __version__
from imagine_mcp.server import (
    _creds_state,
    _get_version,
    _providers_configured,
    _providers_configured_live,
    _set_runtime,
    build_app,
)


def _structured(result: Any) -> dict[str, Any]:
    """Narrow ``ToolResult.structured_content`` for callers below -- also
    pins that dict-returning tools always populate it (never None)."""
    assert result.structured_content is not None
    return result.structured_content


def test_build_app_attributes() -> None:
    app = build_app()
    assert isinstance(app, FastMCP)
    assert app.name == "imagine"
    assert app.instructions is not None
    assert "Image/video understanding and generation" in app.instructions


def test_get_version() -> None:
    assert _get_version() == __version__


def test_build_app_reports_package_version() -> None:
    # serverInfo.version must be the imagine-mcp package version, not the
    # fastmcp package version (which used to leak through as "3.4.2").
    app = build_app()
    reported = app._mcp_server.create_initialization_options().server_version
    assert reported == __version__
    assert reported == _get_version()
    assert reported != "3.4.2"


def test_creds_state(monkeypatch) -> None:
    # No keys
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    assert _creds_state() == "NEEDS_SETUP"

    # One key
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    assert _creds_state() == "CONFIGURED"
    # From store
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with patch(
        "mcp_core.storage.per_plugin_store.PerPluginStore.load",
        return_value={"GEMINI_API_KEY": "test"},
    ):
        assert _creds_state() == "CONFIGURED"


def test_providers_configured(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    assert _providers_configured() == []

    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("XAI_API_KEY", "test")
    assert sorted(_providers_configured()) == ["gemini", "grok", "openai"]


def test_providers_configured_live(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)

    with patch(
        "mcp_core.storage.per_plugin_store.PerPluginStore.load",
        return_value={"OPENAI_API_KEY": "test", "XAI_API_KEY": "test"},
    ):
        res = _providers_configured_live()
        assert "openai" in res
        assert "grok" in res

    monkeypatch.setenv("GEMINI_API_KEY", "test")
    # Coverage for "if provider in seen: continue"
    with patch(
        "imagine_mcp.relay_setup.CREDENTIAL_KEYS", ["GEMINI_API_KEY", "GEMINI_API_KEY"]
    ):
        res = _providers_configured_live()
        assert res == ["gemini"]


def test_set_runtime() -> None:
    # Invalid key
    res = _set_runtime("invalid", "value")
    assert res["status"] == "error"
    assert "Invalid key" in res["message"]

    # Valid key
    res = _set_runtime("log_level", "debug")
    assert res["status"] == "ok"
    assert "Set log_level=debug" in res["message"]


@pytest.mark.asyncio
async def test_tool_help() -> None:
    app = build_app()
    result = await app.call_tool("help", {"topic": "understand"})
    res_text = result.content[0].text
    assert "understand" in res_text.lower()

    result = await app.call_tool("help", {"topic": "invalid"})
    res_text = result.content[0].text
    assert "Unknown topic" in res_text


@pytest.mark.asyncio
async def test_tool_config_basic_actions() -> None:
    app = build_app()

    # status
    result = await app.call_tool("config", {"action": "status"})
    res = _structured(result)
    assert res["version"] == __version__

    # warmup
    result = await app.call_tool("config", {"action": "warmup"})
    res = _structured(result)
    assert res["status"] == "ok"

    # set
    result = await app.call_tool(
        "config", {"action": "set", "key": "log_level", "value": "info"}
    )
    res = _structured(result)
    assert res["status"] == "ok"

    # invalid action
    result = await app.call_tool("config", {"action": "nope"})
    res = _structured(result)
    assert res["status"] == "error"


@pytest.mark.asyncio
async def test_tool_config_cache_clear(monkeypatch) -> None:
    app = build_app()
    monkeypatch.setattr(
        "platformdirs.user_cache_dir", lambda _: "/tmp/imagine-mcp-test"
    )

    with patch("imagine_mcp.cache.ResponseCache.clear") as mock_clear:
        result = await app.call_tool("config", {"action": "cache_clear"})
        res = _structured(result)
        assert res["status"] == "ok"
        mock_clear.assert_called_once()


@pytest.mark.asyncio
async def test_tool_config_models_action_removed() -> None:
    app = build_app()
    result = await app.call_tool("config", {"action": "models"})
    res = _structured(result)
    assert res["status"] == "error"
    assert "Unknown action 'models'" in res["message"]


@pytest.mark.asyncio
async def test_tool_understand_wrapper() -> None:
    app = build_app()
    with patch(
        "imagine_mcp.server.dispatch_understand", return_value={"res": "ok"}
    ) as mock_dispatch:
        result = await app.call_tool(
            "understand", {"media_urls": ["http://ex.com/i.jpg"], "prompt": "tell me"}
        )
        res = _structured(result)
        assert res == {"res": "ok"}
        mock_dispatch.assert_called_once()


@pytest.mark.asyncio
async def test_tool_understand_passes_model_through() -> None:
    app = build_app()
    with patch(
        "imagine_mcp.server.dispatch_understand", return_value={"res": "ok"}
    ) as mock_dispatch:
        await app.call_tool(
            "understand",
            {
                "media_urls": ["http://ex.com/i.jpg"],
                "prompt": "tell me",
                "model": "gemini/gemini-3.1-pro-preview",
            },
        )
        # model is the 6th positional arg of dispatch_understand.
        args, _kwargs = mock_dispatch.call_args
        assert args[5] == "gemini/gemini-3.1-pro-preview"


@pytest.mark.asyncio
async def test_tool_generate_passes_model_through() -> None:
    app = build_app()
    with patch(
        "imagine_mcp.server.dispatch_generate", return_value={"res": "gen"}
    ) as mock_dispatch:
        await app.call_tool(
            "generate",
            {
                "media_type": "image",
                "prompt": "draw me",
                "model": "gemini/gemini-3.1-flash-image-preview",
            },
        )
        # model is the 9th positional arg of dispatch_generate.
        args, _kwargs = mock_dispatch.call_args
        assert args[8] == "gemini/gemini-3.1-flash-image-preview"

    # Test max_media_urls limit
    from imagine_mcp.config import settings

    too_many = ["http://ex.com/i.jpg"] * (settings.max_media_urls + 1)
    with pytest.raises(ToolError, match="Too many media_urls"):
        await app.call_tool("understand", {"media_urls": too_many, "prompt": "tell me"})


@pytest.mark.asyncio
async def test_tool_generate_wrapper() -> None:
    app = build_app()
    with patch(
        "imagine_mcp.server.dispatch_generate", return_value={"res": "gen"}
    ) as mock_dispatch:
        result = await app.call_tool(
            "generate", {"media_type": "image", "prompt": "draw me"}
        )
        res = _structured(result)
        assert res == {"res": "gen"}
        mock_dispatch.assert_called_once()


@pytest.mark.asyncio
async def test_tool_config_relay_actions(monkeypatch) -> None:
    app = build_app()

    # relay_status
    with patch(
        "imagine_mcp.server._providers_configured_live", return_value=["gemini"]
    ):
        result = await app.call_tool("config", {"action": "relay_status"})
        res = _structured(result)
        assert res["status"] == "configured"
        assert res["providers_configured"] == ["gemini"]

    # relay_complete
    with patch("imagine_mcp.server._providers_configured_live", return_value=[]):
        result = await app.call_tool("config", {"action": "relay_complete"})
        res = _structured(result)
        assert res["status"] == "no_credentials"

    # relay_skip (using env)
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    result = await app.call_tool("config", {"action": "relay_skip"})
    res = _structured(result)
    assert res["status"] == "using_env"

    # relay_skip (needs setup)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    result = await app.call_tool("config", {"action": "relay_skip"})
    res = _structured(result)
    assert res["status"] == "needs_setup"

    # relay_reset
    with patch(
        "imagine_mcp.relay_setup.reset_credentials", return_value={"status": "reset"}
    ):
        result = await app.call_tool("config", {"action": "relay_reset"})
        res = _structured(result)
        assert res == {"status": "reset"}


@pytest.mark.asyncio
async def test_tool_config_open_relay() -> None:
    app = build_app()

    # Success
    with patch(
        "imagine_mcp.relay_setup.ensure_config", return_value={"some": "config"}
    ):
        result = await app.call_tool("config", {"action": "open_relay"})
        res = _structured(result)
        assert res["status"] == "saved"

    # Degraded
    with patch("imagine_mcp.relay_setup.ensure_config", return_value=None):
        result = await app.call_tool("config", {"action": "open_relay"})
        res = _structured(result)
        assert res["status"] == "degraded"


@pytest.mark.asyncio
async def test_per_request_sub_scope() -> None:
    from imagine_mcp.credential_state import _current_sub, _request_creds
    from imagine_mcp.server import _per_request_sub_scope

    # Mock next_ function
    async def next_():
        assert _current_sub.get() == "user123"
        assert _request_creds.get() is None

    claims = {"sub": "user123"}
    await _per_request_sub_scope(claims, next_)

    # Verify cleanup
    assert _current_sub.get() is None
    assert _request_creds.get() is None


@pytest.mark.asyncio
async def test_run_http_stdio_local_relay(monkeypatch) -> None:
    from imagine_mcp.server import run_http

    monkeypatch.delenv("PUBLIC_URL", raising=False)

    with patch("mcp_core.transport.local_server.run_http_server") as mock_run:
        await run_http()
        mock_run.assert_called_once()
        _args, kwargs = mock_run.call_args
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["open_browser"] is True


@pytest.mark.asyncio
async def test_run_http_remote_relay(monkeypatch) -> None:
    from imagine_mcp.server import run_http

    monkeypatch.setenv("PUBLIC_URL", "https://ex.com")
    monkeypatch.setenv("MCP_DCR_SERVER_SECRET", "secret")

    with patch("mcp_core.transport.local_server.run_http_server") as mock_run:
        await run_http()
        mock_run.assert_called_once()
        _args, kwargs = mock_run.call_args
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["open_browser"] is False
        assert kwargs["auth_scope"] is not None


@pytest.mark.asyncio
async def test_run_http_remote_relay_custom_host(monkeypatch) -> None:
    from imagine_mcp.server import run_http

    monkeypatch.setenv("PUBLIC_URL", "https://ex.com")
    monkeypatch.setenv("MCP_DCR_SERVER_SECRET", "secret")
    monkeypatch.setenv("MCP_HOST", "192.168.1.100")

    with patch("mcp_core.transport.local_server.run_http_server") as mock_run:
        await run_http()
        mock_run.assert_called_once()
        _args, kwargs = mock_run.call_args
        assert kwargs["host"] == "192.168.1.100"


@pytest.mark.asyncio
async def test_run_http_remote_relay_missing_secret(monkeypatch) -> None:
    from imagine_mcp.server import run_http

    monkeypatch.setenv("PUBLIC_URL", "https://ex.com")
    monkeypatch.delenv("MCP_DCR_SERVER_SECRET", raising=False)

    with pytest.raises(SystemExit, match="imagine-mcp refuses to start"):
        await run_http()


def test_main_calls_run_http() -> None:
    from imagine_mcp.server import main

    async def mock_coro():
        return None

    with patch("asyncio.run") as mock_run:
        coro = mock_coro()
        with patch("imagine_mcp.server.run_http", return_value=coro):
            main()
            mock_run.assert_called_once()
        coro.close()


@pytest.mark.asyncio
async def test_run_http_remote_relay_invalid_port(monkeypatch) -> None:
    from imagine_mcp.server import run_http

    monkeypatch.setenv("PUBLIC_URL", "https://ex.com")
    monkeypatch.setenv("MCP_DCR_SERVER_SECRET", "secret")

    # Test non-integer port
    monkeypatch.setenv("MCP_PORT", "not-a-port")
    with pytest.raises(
        SystemExit, match="imagine-mcp refuses to start: Invalid MCP_PORT"
    ):
        await run_http()

    # Test negative port
    monkeypatch.setenv("MCP_PORT", "-1")
    with pytest.raises(
        SystemExit, match="imagine-mcp refuses to start: Invalid MCP_PORT"
    ):
        await run_http()

    # Test out of range port
    monkeypatch.setenv("MCP_PORT", "70000")
    with pytest.raises(
        SystemExit, match="imagine-mcp refuses to start: Invalid MCP_PORT"
    ):
        await run_http()


@pytest.mark.asyncio
async def test_run_http_remote_relay_invalid_host(monkeypatch) -> None:
    from imagine_mcp.server import run_http

    monkeypatch.setenv("PUBLIC_URL", "https://ex.com")
    monkeypatch.setenv("MCP_DCR_SERVER_SECRET", "secret")

    # Test malformed IP
    monkeypatch.setenv("MCP_HOST", "999.999.999.999")
    with pytest.raises(
        SystemExit, match="imagine-mcp refuses to start: Invalid MCP_HOST IP address"
    ):
        await run_http()

    # Test invalid hostname format
    monkeypatch.setenv("MCP_HOST", "invalid host name")
    with pytest.raises(
        SystemExit, match="imagine-mcp refuses to start: Invalid MCP_HOST hostname"
    ):
        await run_http()
