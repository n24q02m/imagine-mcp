from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from imagine_mcp.errors import ProviderUnsupportedError
from imagine_mcp.providers import grok as provider


@pytest.fixture
def mock_media_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock async media fetchers to avoid real network calls."""
    mock_resp = MagicMock()
    mock_resp.content = b"fake-image-bytes"
    mock_resp.headers = {"content-type": "image/png"}

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.post.return_value = mock_resp

    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )


@pytest.mark.asyncio
async def test_understand_video_raises() -> None:
    with pytest.raises(ProviderUnsupportedError):
        await provider.understand_video("https://example.com/x.mp4", "describe", "poor")


@pytest.mark.asyncio
async def test_understand_image_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    msg = MagicMock()
    msg.content = "a parrot"
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]

    captured: dict[str, object] = {}

    async def fake_acompletion(**kwargs: object) -> object:
        captured.update(kwargs)
        return resp

    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    monkeypatch.setattr("mcp_core.llm.acompletion", fake_acompletion)

    result = await provider.understand_image(
        url="https://example.com/parrot.png", prompt="describe", tier="rich"
    )
    assert result["text"] == "a parrot"
    assert result["model"] == "grok-4.20-0309-reasoning"
    assert result["provider"] == "grok"
    # litellm passthrough: model is prefixed with the xai/ provider route and
    # the resolved (non-empty) api_key is forwarded.
    assert captured["model"] == "xai/grok-4.20-0309-reasoning"
    assert captured["api_key"] == "xai-test"
