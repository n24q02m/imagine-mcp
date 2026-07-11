"""S13 W1.1 pin: outputSchema + structuredContent for imagine-mcp tools.

Verifies FastMCP's automatic structured-output derivation for the
``-> dict[str, Any]`` tools (understand/generate/config) and pins the
degenerate string-wrap behavior for ``help`` (kept ``-> str`` by design,
see ``.superpowers/sdd/plan.md`` Global Constraints #1-2).
"""

from __future__ import annotations

import json

import pytest
from fastmcp import Client

from imagine_mcp.server import build_app

_DICT_TOOLS = {"understand", "generate", "config"}


@pytest.fixture
def app():
    return build_app()


async def test_dict_tools_expose_object_output_schema(app) -> None:
    """understand/generate/config -> dict[str, Any] auto-derives a loose
    object outputSchema (envelope-lỏng per plan Global Constraint 1)."""
    async with Client(app) as client:
        tools = await client.list_tools()

    by_name = {t.name: t for t in tools}
    for name in _DICT_TOOLS:
        schema = by_name[name].outputSchema
        assert schema is not None, f"{name} missing outputSchema"
        assert schema["type"] == "object"
        assert schema.get("additionalProperties") is True


async def test_help_keeps_degenerate_string_wrap(app) -> None:
    """help() stays -> str by design; FastMCP wraps it as {"result": <str>}
    (x-fastmcp-wrap-result) instead of a useful object schema. Pinned so a
    future edit doesn't "fix" help into dict[str, Any] by mistake."""
    async with Client(app) as client:
        tools = await client.list_tools()
        result = await client.call_tool("help", {"topic": "understand"})

    schema = next(t for t in tools if t.name == "help").outputSchema
    assert schema is not None
    assert schema.get("x-fastmcp-wrap-result") is True
    assert schema.get("additionalProperties") is None
    assert schema["properties"].keys() == {"result"}

    assert result.structured_content == {"result": result.content[0].text}
    assert "understand" in result.content[0].text.lower()


async def test_config_call_emits_structured_content_matching_text(app) -> None:
    """config(action="status") -> dict dual-emits: structuredContent carries
    the dict directly, and the legacy TextContent JSON decodes to the same
    payload (backward-compat wire per plan Global Constraint 5)."""
    async with Client(app) as client:
        result = await client.call_tool("config", {"action": "status"})

    assert isinstance(result.structured_content, dict)
    assert result.structured_content["version"]
    assert json.loads(result.content[0].text) == result.structured_content
