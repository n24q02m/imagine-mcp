from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from imagine_mcp import dispatcher
from imagine_mcp.providers import gemini, grok
from imagine_mcp.providers import openai as openai_provider


@pytest.mark.asyncio
async def test_dispatch_generate_forwards_output_mode(monkeypatch):
    captured = {}

    async def fake_generate_image(
        prompt, tier, reference_image_url, aspect_ratio, output_mode, model_id=None
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
        prompt, tier, reference_image_url, aspect_ratio, output_mode, model_id=None
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


@pytest.mark.asyncio
async def test_gemini_generate_image_base64_no_disk(monkeypatch, tmp_path):
    # Any disk write would land under this redirected cache dir.
    monkeypatch.setattr("platformdirs.user_cache_dir", lambda *a, **k: str(tmp_path))
    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock()
    fake_part = MagicMock()
    fake_part.inline_data.data = b"\x89PNG_fake_bytes"
    fake_response = MagicMock()
    fake_response.candidates = [MagicMock()]
    fake_response.candidates[0].content.parts = [fake_part]
    fake_client.aio.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    out = await gemini.generate_image(prompt="a cat", tier="poor", output_mode="base64")

    assert out.get("image_base64")
    assert "image_path" not in out  # path suppressed
    assert not (tmp_path / "generations").exists()  # NOTHING written to disk


@pytest.mark.asyncio
async def test_gemini_generate_image_both_writes_path(monkeypatch, tmp_path):
    monkeypatch.setattr("platformdirs.user_cache_dir", lambda *a, **k: str(tmp_path))
    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock()
    fake_part = MagicMock()
    fake_part.inline_data.data = b"\x89PNG_fake_bytes"
    fake_response = MagicMock()
    fake_response.candidates = [MagicMock()]
    fake_response.candidates[0].content.parts = [fake_part]
    fake_client.aio.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    out = await gemini.generate_image(prompt="a cat", tier="poor", output_mode="both")

    assert "image_base64" in out and "image_path" in out  # back-compat default
    assert (tmp_path / "generations").exists()


@pytest.mark.asyncio
async def test_gemini_generate_video_base64_no_path(monkeypatch, tmp_path):
    monkeypatch.setattr("platformdirs.user_cache_dir", lambda *a, **k: str(tmp_path))
    fake_client = MagicMock()
    fake_op = MagicMock()
    fake_op.done = True
    fake_op.error = None
    fake_video = MagicMock()
    fake_op.response.generated_videos = [fake_video]
    fake_client.aio.operations.get = AsyncMock(return_value=fake_op)
    # google-genai 2.8.0: the ASYNC files.download RETURNS the bytes and (unlike
    # the sync client) does NOT set video.video.video_bytes as a side effect, so
    # the impl reads the return value -- the fake returns the bytes here.
    fake_client.aio.files.download = AsyncMock(return_value=b"FAKEMP4")
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    out = await gemini.generate_video(
        prompt="a wave", tier="poor", job_id="op/123", output_mode="base64"
    )
    assert "video_base64" in out and "video_path" not in out
    assert not (tmp_path / "generations").exists()


@pytest.mark.asyncio
async def test_openai_generate_image_base64_no_disk(monkeypatch, tmp_path):
    monkeypatch.setattr("platformdirs.user_cache_dir", lambda *a, **k: str(tmp_path))
    import base64 as _b64

    fake_client = MagicMock()
    fake_resp = MagicMock()
    fake_resp.data = [MagicMock(b64_json=_b64.b64encode(b"PNGDATA").decode())]
    fake_client.images.generate = AsyncMock(return_value=fake_resp)
    monkeypatch.setattr(openai_provider, "_client", lambda: fake_client)

    out = await openai_provider.generate_image(
        prompt="a cat", tier="poor", output_mode="base64"
    )
    assert "image_base64" in out and "image_path" not in out
    assert not (tmp_path / "generations").exists()


@pytest.mark.asyncio
async def test_grok_generate_image_base64_no_disk(monkeypatch, tmp_path):
    import base64 as _b64

    monkeypatch.setattr("platformdirs.user_cache_dir", lambda *a, **k: str(tmp_path))
    monkeypatch.setattr(grok, "_api_key", lambda: "dummy")

    resp = MagicMock()
    resp.status_code = 200
    resp.json = lambda: {"data": [{"b64_json": _b64.b64encode(b"PNGDATA").decode()}]}
    fake_client = MagicMock()
    fake_client.post = AsyncMock(return_value=resp)
    # grok.py binds the name at import time (grok.py:22
    # `from imagine_mcp.media import get_ssrf_safe_async_client`), so patch the
    # symbol IN grok's module namespace -- patching imagine_mcp.media would NOT
    # affect grok's already-bound reference.
    monkeypatch.setattr(
        "imagine_mcp.providers.grok.get_ssrf_safe_async_client", lambda: fake_client
    )

    out = await grok.generate_image(prompt="a cat", tier="poor", output_mode="base64")
    assert "image_base64" in out and "image_path" not in out
    assert not (tmp_path / "generations").exists()
