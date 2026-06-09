"""Verify the tools are registered and tool validation works (in-process)."""

from __future__ import annotations

import asyncio

from imagine_mcp.server import VALID_HELP_TOPICS, build_app


def test_tools_registered() -> None:
    app = build_app()
    tools = asyncio.run(app.list_tools())
    tool_names = {t.name for t in tools}
    # 4 product tools + config__open_relay (Transparent Bridge Wave 3, mcp-core v1.11+).
    assert tool_names == {
        "understand",
        "generate",
        "config",
        "help",
        "config__open_relay",
    }


def test_help_topic_set() -> None:
    assert {"understand", "generate", "config"} == VALID_HELP_TOPICS


def test_tools_have_non_empty_descriptions() -> None:
    # config__open_relay is registered by mcp-core's helper and inherits its
    # docstring; FastMCP does not lift it onto FunctionTool.description, so we
    # only enforce the description contract on the 4 product tools defined here.
    app = build_app()
    tools = asyncio.run(app.list_tools())
    for t in tools:
        if t.name == "config__open_relay":
            continue
        assert t.description, f"tool {t.name} has empty description"
        assert len(t.description) >= 20
