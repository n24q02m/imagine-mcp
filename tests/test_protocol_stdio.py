"""Protocol-level test: drive the server over stdio the way a real client does.

The rest of the suite calls Python functions directly, which cannot catch a
break in tool registration, the generated argument schema, or the stdio
transport itself -- a server can be perfectly correct in-process and still be
unusable from an MCP client. This test spawns the server as a subprocess and
talks to it through ``mcp.ClientSession``.

It exercises ``generate``, the tool this server exists for. ``config`` /
``help`` round-trips are deliberately not the subject: they would pass on a
server whose generation path is entirely broken.

Marked ``live`` because it spends real provider credit. ``addopts`` in
pyproject.toml is ``-m 'not live'``, so CI and pre-commit never run it. Run it
deliberately, with credentials injected from skret ``/imagine-mcp/prod``::

    skret run -e prod -- uv run pytest -m live tests/test_protocol_stdio.py -s
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import sys
from typing import Any

import pytest

# The stdio server reads credentials from the environment only. At least one
# provider key is enough -- the dispatcher auto-selects a provider in the order
# XAI -> OpenAI -> Gemini from whichever keys are present.
PROVIDER_KEYS = ("XAI_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY")

# Enough to identify the bytes as a real image without pulling in an image lib.
IMAGE_MAGIC = {
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
}


def _configured_provider_keys() -> list[str]:
    return [name for name in PROVIDER_KEYS if os.environ.get(name)]


def _sniff_image(data: bytes) -> str | None:
    for magic, kind in IMAGE_MAGIC.items():
        if data.startswith(magic):
            return kind
    # WebP is RIFF....WEBP -- the size field sits between the two markers.
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _payload(result: Any) -> dict[str, Any]:
    """Pull the tool's dict result out of a CallToolResult.

    Prefers ``structuredContent``; older servers only fill ``content`` with a
    JSON text block. Raises rather than returning a partial dict, so a shape
    change surfaces as a failure instead of a missing-key assertion later.
    """
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict) and structured:
        return structured

    text = "".join(getattr(block, "text", "") for block in result.content)
    if not text:
        raise AssertionError("tool result carried neither structuredContent nor text")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"tool result is not JSON: {text[:300]}") from exc
    if not isinstance(parsed, dict):
        raise AssertionError(f"expected a dict result, got {type(parsed).__name__}")
    return parsed


# 600s overrides the suite-wide 30s cap in pyproject: this waits on a real
# upstream image generation, not on local code.
@pytest.mark.live
@pytest.mark.timeout(600)
async def test_generate_image_over_stdio_protocol() -> None:
    """`generate` returns real image bytes when driven through MCP stdio.

    The skip below is the only non-failure exit, and it is decided purely from
    the environment *before* the server is launched. Once the subprocess
    starts, every outcome is a failure: a missing credential can no longer be
    confused with a broken server.

    That split is deliberate in one direction that looks harsh. A credential
    that is present but *rejected upstream* fails loudly here rather than
    skipping, because a dead key that skips is indistinguishable from a key
    that was never configured -- and a whole stack can sit on an expired
    credential for weeks on the strength of a green suite.
    """
    configured = _configured_provider_keys()
    if not configured:
        pytest.skip(
            "no provider credential in the environment -- set one of "
            f"{', '.join(PROVIDER_KEYS)} (skret namespace /imagine-mcp/prod, "
            "e.g. `skret run -e prod -- uv run pytest -m live`). "
            "This is a missing precondition, not a server failure."
        )

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    # Run the server out of this checkout, not a published wheel: the point is
    # to test the code under review. stdio_client merges this over its own
    # minimal environment, which does not forward API keys, so the credential
    # has to be passed explicitly.
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "imagine_mcp"],
        env={name: os.environ[name] for name in configured},
    )

    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        tool_names = {tool.name for tool in (await session.list_tools()).tools}
        assert "generate" in tool_names, (
            f"generate is not registered over stdio; got {sorted(tool_names)}"
        )

        result = await session.call_tool(
            "generate",
            {
                "media_type": "image",
                "prompt": "a red circle",
                "tier": "poor",
                # base64 keeps the assertion on the returned bytes and writes
                # nothing to the user's cache directory.
                "output_mode": "base64",
            },
        )

    assert not result.isError, f"generate reported an error: {result.content}"

    payload = _payload(result)
    assert "image_base64" in payload, (
        f"expected image_base64 in the result, got keys {sorted(payload)}"
    )

    encoded = payload["image_base64"]
    assert encoded, "image_base64 is present but empty"

    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AssertionError(f"image_base64 is not valid base64: {exc}") from exc

    # Assert on the bytes rather than the field: a provider that returned an
    # error string or a zero-length body would still satisfy "key is present".
    kind = _sniff_image(raw)
    assert kind is not None, (
        f"decoded {len(raw)} bytes are not a recognised image "
        f"(first 16 bytes: {raw[:16]!r})"
    )

    print(
        f"\nprotocol OK: provider key {configured[0]}, "
        f"{kind} image, {len(raw)} bytes decoded from image_base64"
    )
