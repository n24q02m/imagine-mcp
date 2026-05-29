from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from imagine_mcp.errors import ProviderUnsupportedError
from imagine_mcp.providers import openai as provider


@pytest.fixture
def mock_media_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock get_ssrf_safe_client to avoid real network calls."""
    mock_resp = MagicMock()
    mock_resp.content = b"fake-image-bytes"
    mock_resp.headers = {"content-type": "image/png"}

    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: mock_client)


def test_understand_video_raises() -> None:
    with pytest.raises(ProviderUnsupportedError):
        provider.understand_video("https://example.com/x.mp4", "describe", "poor")


def test_generate_video_raises() -> None:
    with pytest.raises(ProviderUnsupportedError):
        provider.generate_video("a dog", "poor")


def test_video_status_raises() -> None:
    with pytest.raises(ProviderUnsupportedError):
        provider.video_status("poor", "job_123")


def test_edit_mocked(mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = MagicMock()
    # Mock images.edit response
    mock_image = MagicMock()
    mock_image.b64_json = "ZmFrZS1pbWFnZS1ieXRlcw=="  # "fake-image-bytes" in base64
    fake.images.edit.return_value = MagicMock(data=[mock_image])
    monkeypatch.setattr(provider, "_client", lambda: fake)

    result = provider.edit(
        tier="poor", image_url="https://example.com/cat.png", prompt="make it blue"
    )
    assert "generations" in result["image_path"]
    assert result["image_base64"] == "ZmFrZS1pbWFnZS1ieXRlcw=="
    assert result["model"] == "dall-e-2"
    assert result["provider"] == "openai"


def test_generate_image_delegates_to_edit(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = MagicMock()
    # Mock images.edit response
    mock_image = MagicMock()
    mock_image.b64_json = "ZmFrZS1pbWFnZS1ieXRlcw=="
    fake.images.edit.return_value = MagicMock(data=[mock_image])
    monkeypatch.setattr(provider, "_client", lambda: fake)

    # Calling generate_image with reference_image_url should trigger edit
    result = provider.generate_image(
        prompt="make it blue",
        tier="poor",
        reference_image_url="https://example.com/cat.png",
    )
    assert result["model"] == "dall-e-2"
    assert result["provider"] == "openai"


def test_understand_image_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = MagicMock()
    fake.responses.create.return_value = MagicMock(output_text="a dog")
    monkeypatch.setattr(provider, "_client", lambda: fake)

    result = provider.understand_image(
        url="https://example.com/dog.png", prompt="describe", tier="poor"
    )
    assert result["text"] == "a dog"
    assert result["model"] == "gpt-5.4-mini"
    assert result["provider"] == "openai"
