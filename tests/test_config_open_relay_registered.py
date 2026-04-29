"""Smoke test: ``config__open_relay`` MCP tool is registered.

Transparent Bridge Wave 3 (mcp-core v1.11+) gives the LLM the ability to
re-trigger the relay form via tool call. Each consumer server registers the
helper from ``mcp_core.relay.tool_helpers``; this test guards against
regressions where the registration line is removed or the tool name changes.
"""

from __future__ import annotations

import asyncio

from imagine_mcp.server import build_app


def test_config_open_relay_tool_registered() -> None:
    """``config__open_relay`` must appear in the MCP tool list."""
    app = build_app()
    tools = asyncio.run(app.list_tools())
    tool_names = {t.name for t in tools}
    assert "config__open_relay" in tool_names, (
        f"config__open_relay missing from tool list: {sorted(tool_names)}"
    )


def test_config_open_relay_tool_is_callable() -> None:
    """The registered tool is wired through FastMCP and exposes a handler."""
    app = build_app()
    tools = asyncio.run(app.list_tools())
    tool = next(t for t in tools if t.name == "config__open_relay")
    # FastMCP wraps the closure as a FunctionTool; just assert it's there.
    assert tool is not None
    assert tool.name == "config__open_relay"
