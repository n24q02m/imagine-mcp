from __future__ import annotations

import pytest

from imagine_mcp.server import _is_valid_host, run_http


def test_is_valid_host():
    # Valid IPs
    assert _is_valid_host("127.0.0.1") is True
    assert _is_valid_host("8.8.8.8") is True
    assert _is_valid_host("::1") is True

    # Valid Hostnames
    assert _is_valid_host("localhost") is True
    assert _is_valid_host("example.com") is True
    assert _is_valid_host("my-server.internal") is True
    assert _is_valid_host("a.b.c") is True

    # Invalid hosts
    assert _is_valid_host("") is False
    assert _is_valid_host(" ") is False
    assert _is_valid_host("-leading.dash") is False
    assert _is_valid_host("trailing.dash-") is False
    assert _is_valid_host("invalid_underscore") is False
    assert _is_valid_host("host name with spaces") is False
    assert _is_valid_host("toolong" * 50) is False


@pytest.mark.asyncio
async def test_run_http_invalid_host(monkeypatch):
    monkeypatch.setenv("PUBLIC_URL", "https://example.com")
    monkeypatch.setenv("MCP_DCR_SERVER_SECRET", "secret")
    monkeypatch.setenv("MCP_HOST", "invalid host")

    with pytest.raises(SystemExit) as excinfo:
        await run_http()
    assert "Invalid MCP_HOST" in str(excinfo.value)


@pytest.mark.asyncio
async def test_run_http_invalid_port(monkeypatch):
    monkeypatch.setenv("PUBLIC_URL", "https://example.com")
    monkeypatch.setenv("MCP_DCR_SERVER_SECRET", "secret")
    monkeypatch.setenv("MCP_PORT", "99999")

    with pytest.raises(SystemExit) as excinfo:
        await run_http()
    assert "Invalid MCP_PORT" in str(excinfo.value)


@pytest.mark.asyncio
async def test_run_http_non_numeric_port(monkeypatch):
    monkeypatch.setenv("PUBLIC_URL", "https://example.com")
    monkeypatch.setenv("MCP_DCR_SERVER_SECRET", "secret")
    monkeypatch.setenv("MCP_PORT", "abc")

    with pytest.raises(SystemExit) as excinfo:
        await run_http()
    assert "Invalid MCP_PORT" in str(excinfo.value)
