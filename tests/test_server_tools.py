"""Verify the 4 tools are registered and tool validation works (in-process)."""

from __future__ import annotations

import asyncio

from imagine_mcp.server import VALID_HELP_TOPICS, build_app


def test_four_tools_registered() -> None:
    app = build_app()
    tools = asyncio.run(app.list_tools())
    tool_names = {t.name for t in tools}
    assert tool_names == {"understand", "generate", "config", "help"}


def test_help_topic_set() -> None:
    assert VALID_HELP_TOPICS == {"understand", "generate", "config"}


def test_tools_have_non_empty_descriptions() -> None:
    app = build_app()
    tools = asyncio.run(app.list_tools())
    for t in tools:
        assert t.description, f"tool {t.name} has empty description"
        assert len(t.description) >= 20
