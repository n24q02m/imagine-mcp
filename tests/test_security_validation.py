from unittest.mock import patch

import pytest

from imagine_mcp.server import run_http


@pytest.mark.asyncio
async def test_run_http_public_url_validation(monkeypatch):
    monkeypatch.setenv("MCP_DCR_SERVER_SECRET", "secret")

    # Invalid scheme
    monkeypatch.setenv("PUBLIC_URL", "javascript:alert(1)")
    with pytest.raises(SystemExit, match="Invalid PUBLIC_URL scheme"):
        await run_http()

    # Missing hostname
    monkeypatch.setenv("PUBLIC_URL", "http://")
    with pytest.raises(SystemExit, match="missing hostname"):
        await run_http()


@pytest.mark.asyncio
async def test_run_http_port_validation(monkeypatch):
    monkeypatch.setenv("PUBLIC_URL", "https://example.com")
    monkeypatch.setenv("MCP_DCR_SERVER_SECRET", "secret")

    # Not an integer
    monkeypatch.setenv("MCP_PORT", "not-a-port")
    with pytest.raises(SystemExit, match="Invalid MCP_PORT 'not-a-port'"):
        await run_http()

    # Out of range (high)
    monkeypatch.setenv("MCP_PORT", "70000")
    with pytest.raises(SystemExit, match="Invalid MCP_PORT '70000'"):
        await run_http()

    # Out of range (low)
    monkeypatch.setenv("MCP_PORT", "-1")
    with pytest.raises(SystemExit, match="Invalid MCP_PORT '-1'"):
        await run_http()


@pytest.mark.asyncio
async def test_run_http_host_validation(monkeypatch):
    monkeypatch.setenv("PUBLIC_URL", "https://example.com")
    monkeypatch.setenv("MCP_DCR_SERVER_SECRET", "secret")

    # Malformed hostname
    monkeypatch.setenv("MCP_HOST", "not_a_host_!")
    with pytest.raises(SystemExit, match="Invalid MCP_HOST 'not_a_host_!'"):
        await run_http()

    # Invalid IP
    monkeypatch.setenv("MCP_HOST", "999.999.999.999")
    with pytest.raises(SystemExit, match=r"Invalid MCP_HOST '999.999.999.999'"):
        await run_http()

    # Valid hostname should pass
    monkeypatch.setenv("MCP_HOST", "valid-host.local")
    with (
        patch("mcp_core.transport.local_server.run_http_server") as mock_run,
        patch("imagine_mcp.server.build_app"),
    ):
        # We also need to patch run_http_server to return immediately
        mock_run.return_value = None
        await run_http()
        mock_run.assert_called_once()
        assert mock_run.call_args[1]["host"] == "valid-host.local"

    # Valid IP should pass
    monkeypatch.setenv("MCP_HOST", "1.1.1.1")
    with (
        patch("mcp_core.transport.local_server.run_http_server") as mock_run,
        patch("imagine_mcp.server.build_app"),
    ):
        mock_run.return_value = None
        await run_http()
        mock_run.assert_called_once()
        assert mock_run.call_args[1]["host"] == "1.1.1.1"
