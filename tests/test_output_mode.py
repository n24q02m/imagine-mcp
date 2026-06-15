from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from imagine_mcp import dispatcher


@pytest.mark.asyncio
async def test_dispatch_generate_forwards_output_mode(monkeypatch):
    captured = {}

    async def fake_generate_image(
        prompt, tier, reference_image_url, aspect_ratio, output_mode
    ):
        captured["output_mode"] = output_mode
        return {"image_base64": "x", "model": "m", "provider": "gemini", "tier": tier}

    fake_mod = AsyncMock()
    fake_mod.generate_image = fake_generate_image
    monkeypatch.setattr(dispatcher, "_load_provider", lambda p: fake_mod)
    monkeypatch.setattr(dispatcher, "_default_provider", lambda: "gemini")
    monkeypatch.delenv("IMAGINE_OUTPUT_MODE", raising=False)

    await dispatcher.dispatch_generate(
        "image", "a cat", "gemini", "poor", output_mode="base64"
    )
    assert captured["output_mode"] == "base64"


@pytest.mark.asyncio
async def test_env_override_wins_over_tool_arg(monkeypatch):
    captured = {}

    async def fake_generate_image(
        prompt, tier, reference_image_url, aspect_ratio, output_mode
    ):
        captured["output_mode"] = output_mode
        return {"image_base64": "x"}

    fake_mod = AsyncMock()
    fake_mod.generate_image = fake_generate_image
    monkeypatch.setattr(dispatcher, "_load_provider", lambda p: fake_mod)
    monkeypatch.setattr(dispatcher, "_default_provider", lambda: "gemini")
    monkeypatch.setenv("IMAGINE_OUTPUT_MODE", "base64")

    # caller asked for "both" but the deploy-level env forces base64
    await dispatcher.dispatch_generate(
        "image", "a cat", "gemini", "poor", output_mode="both"
    )
    assert captured["output_mode"] == "base64"
