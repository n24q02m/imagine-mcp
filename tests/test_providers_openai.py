from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock

import pytest

from imagine_mcp.errors import ProviderAPIError, ProviderUnsupportedError
from imagine_mcp.providers import openai as provider


@pytest.fixture
def mock_media_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock async media fetchers to avoid real network calls."""
    mock_resp = MagicMock()
    mock_resp.content = b"fake-image-bytes"
    mock_resp.headers = {"content-type": "image/png"}

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp

    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )


@pytest.mark.asyncio
async def test_understand_video_raises() -> None:
    with pytest.raises(ProviderUnsupportedError):
        await provider.understand_video("https://example.com/x.mp4", "describe", "poor")


@pytest.mark.asyncio
async def test_generate_video_raises() -> None:
    with pytest.raises(ProviderUnsupportedError):
        await provider.generate_video("a dog", "poor")


@pytest.mark.asyncio
async def test_understand_image_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    # understand_image is litellm passthrough via mcp_core.llm (mocked).
    msg = MagicMock()
    msg.content = "a dog"
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]

    captured: dict[str, object] = {}

    async def fake_acompletion(**kwargs: object) -> object:
        captured.update(kwargs)
        return resp

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr("mcp_core.llm.acompletion", fake_acompletion)

    result = await provider.understand_image(
        url="https://example.com/dog.png", prompt="describe", tier="poor"
    )
    assert result["text"] == "a dog"
    assert result["model"] == "gpt-5.4-mini"
    assert result["provider"] == "openai"
    assert captured["model"] == "openai/gpt-5.4-mini"
    assert captured["api_key"] == "sk-test"


@pytest.mark.asyncio
async def test_generate_image_basic_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_resp = MagicMock()
    mock_item = MagicMock()
    mock_item.b64_json = base64.b64encode(b"generated-image").decode()
    mock_resp.data = [mock_item]

    captured: dict[str, object] = {}

    async def fake_aimage_generation(**kwargs: object) -> object:
        captured.update(kwargs)
        return mock_resp

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr("mcp_core.llm.aimage_generation", fake_aimage_generation)

    async def fake_emit_media(data, suffix, key, output_mode):
        assert data == b"generated-image"
        return {"image_base64": "fake-b64", "image_path": "fake/path.png"}

    monkeypatch.setattr("imagine_mcp.media.emit_media", fake_emit_media)

    result = await provider.generate_image(
        prompt="a sunset", tier="poor", aspect_ratio="16:9"
    )

    assert result["image_path"] == "fake/path.png"
    assert result["model"] == "gpt-image-1-mini"
    assert result["provider"] == "openai"
    assert result["tier"] == "poor"
    assert captured["model"] == "openai/gpt-image-1-mini"
    assert captured["prompt"] == "a sunset"
    assert captured["size"] == "1792x1024"
    assert captured["api_key"] == "sk-test"


@pytest.mark.asyncio
async def test_generate_image_edit_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_resp = MagicMock()
    mock_item = MagicMock()
    mock_item.b64_json = base64.b64encode(b"edited-image").decode()
    mock_resp.data = [mock_item]

    mock_client_inst = MagicMock()
    mock_client_inst.images.edit = AsyncMock(return_value=mock_resp)

    monkeypatch.setattr(provider, "_client", lambda: mock_client_inst)

    async def fake_emit_media(data, suffix, key, output_mode):
        assert data == b"edited-image"
        return {"image_path": "fake/edited.png"}

    monkeypatch.setattr("imagine_mcp.media.emit_media", fake_emit_media)

    result = await provider.generate_image(
        prompt="add a cat",
        tier="rich",
        reference_image_url="https://example.com/ref.png",
        aspect_ratio="1:1",
    )

    assert result["image_path"] == "fake/edited.png"
    assert result["model"] == "gpt-image-1.5"
    mock_client_inst.images.edit.assert_called_once_with(
        model="gpt-image-1.5",
        image=b"fake-image-bytes",
        prompt="add a cat",
        size="1024x1024",
    )


@pytest.mark.asyncio
async def test_generate_image_no_data_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_resp = MagicMock()
    mock_item = MagicMock()
    mock_item.b64_json = None
    mock_resp.data = [mock_item]

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(
        "mcp_core.llm.aimage_generation", AsyncMock(return_value=mock_resp)
    )

    with pytest.raises(ProviderAPIError, match="OpenAI returned no image"):
        await provider.generate_image(prompt="nothing", tier="poor")


@pytest.mark.asyncio
async def test_generate_image_model_override(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_resp = MagicMock()
    mock_item = MagicMock()
    mock_item.b64_json = base64.b64encode(b"overridden").decode()
    mock_resp.data = [mock_item]

    captured: dict[str, object] = {}

    async def fake_aimage_generation(**kwargs: object) -> object:
        captured.update(kwargs)
        return mock_resp

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr("mcp_core.llm.aimage_generation", fake_aimage_generation)
    monkeypatch.setattr("imagine_mcp.media.emit_media", AsyncMock(return_value={}))

    await provider.generate_image(
        prompt="override", tier="poor", model_id="dall-e-3-experimental"
    )
    assert captured["model"] == "openai/dall-e-3-experimental"


@pytest.mark.asyncio
async def test_reset_client() -> None:
    # Coverage for _reset_client
    provider._reset_client()


def test_client_factory() -> None:
    # Coverage for _client_factory
    from openai import AsyncOpenAI

    client = provider._client_factory(api_key="sk-test")
    assert isinstance(client, AsyncOpenAI)
    assert client.api_key == "sk-test"


def test_get_client(monkeypatch: pytest.MonkeyPatch) -> None:
    # Coverage for _client()
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    client = provider._client()
    from openai import AsyncOpenAI

    assert isinstance(client, AsyncOpenAI)
