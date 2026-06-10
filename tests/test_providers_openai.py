from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from imagine_mcp.errors import ProviderUnsupportedError
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
    fake = MagicMock()
    fake.responses.create = AsyncMock(return_value=MagicMock(output_text="a dog"))
    monkeypatch.setattr(provider, "_client", lambda: fake)

    result = await provider.understand_image(
        url="https://example.com/dog.png", prompt="describe", tier="poor"
    )
    assert result["text"] == "a dog"
    assert result["model"] == "gpt-5.4-mini"
    assert result["provider"] == "openai"
