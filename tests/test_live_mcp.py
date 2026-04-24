"""MCP protocol E2E test: spawn server subprocess via stdio_client.

Run with: uv run pytest tests/test_live_mcp.py -v -m mcp_protocol
"""
# ruff: noqa: SIM117

from __future__ import annotations

import pytest

pytestmark = pytest.mark.mcp_protocol


def test_mcp_protocol_lists_four_tools() -> None:
    import asyncio

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command="uv",
        args=["run", "imagine-mcp", "--stdio"],
        env=None,
    )

    async def _run() -> set[str]:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                return {t.name for t in tools.tools}

    tool_names = asyncio.run(_run())
    assert tool_names == {"understand", "generate", "config", "help"}


def test_mcp_protocol_help_topic_config() -> None:
    import asyncio

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command="uv",
        args=["run", "imagine-mcp", "--stdio"],
        env=None,
    )

    async def _run() -> str:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("help", {"topic": "config"})
                for content in result.content:
                    if content.type == "text":
                        return content.text
                return ""

    text = asyncio.run(_run())
    assert "config tool" in text.lower()
    assert len(text) >= 100


def test_mcp_protocol_config_status() -> None:
    import asyncio
    import json

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command="uv",
        args=["run", "imagine-mcp", "--stdio"],
        env=None,
    )

    async def _run() -> dict:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("config", {"action": "status"})
                for content in result.content:
                    if content.type == "text":
                        return json.loads(content.text)
                return {}

    status = asyncio.run(_run())
    assert "credentials_state" in status
    assert status["credentials_state"] in ("CONFIGURED", "NEEDS_SETUP")
    assert "providers_configured" in status
    assert "default_provider" in status
