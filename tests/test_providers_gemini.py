from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

from imagine_mcp.providers import gemini


def test_understand_image_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.text = "a cat on a mat"
    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    result = gemini.understand_image(
        url="https://example.com/cat.png", prompt="describe", tier="poor"
    )
    assert result["text"] == "a cat on a mat"
    assert result["model"] == "gemini-3.1-flash-lite-preview"
    assert result["provider"] == "gemini"
    assert result["tier"] == "poor"


def test_understand_video_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.text = "a cat jumping"
    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    result = gemini.understand_video(
        url="https://example.com/cat.mp4", prompt="describe", tier="rich"
    )
    assert result["text"] == "a cat jumping"
    assert result["model"] == "gemini-3.1-pro-preview"


@pytest.mark.live
def test_understand_image_live() -> None:
    """Live test against real Gemini API."""
    if not os.environ.get("GEMINI_API_KEY"):
        pytest.skip("Requires GEMINI_API_KEY")

    gemini._reset_client()
    result = gemini.understand_image(
        url=(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/"
            "Cat_November_2010-1a.jpg/300px-Cat_November_2010-1a.jpg"
        ),
        prompt="What animal is in this image? Answer in one word.",
        tier="poor",
    )
    assert "cat" in result["text"].lower()


def test_understand_multimodal_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.text = "mixed content"
    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    # Use a mock for detect_media_type to verify it is NOT called when media_types is provided
    mock_detect = MagicMock()
    monkeypatch.setattr("imagine_mcp.media.detect_media_type", mock_detect)

    urls = ["https://example.com/cat.png", "https://example.com/dog.mp4"]
    media_types = ["image", "video"]
    result = gemini.understand_multimodal(
        urls=urls, prompt="describe both", tier="poor", media_types=media_types
    )

    assert result["text"] == "mixed content"
    assert result["multimodal"] is True
    assert mock_detect.call_count == 0


def test_understand_multimodal_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.text = "mixed content fallback"
    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    # Use a mock for detect_media_type to verify it IS called when media_types is NOT provided
    mock_detect = MagicMock(return_value="image")
    monkeypatch.setattr("imagine_mcp.media.detect_media_type", mock_detect)

    urls = ["https://example.com/cat.png", "https://example.com/dog.png"]
    result = gemini.understand_multimodal(
        urls=urls, prompt="describe both", tier="poor"
    )

    assert result["text"] == "mixed content fallback"
    assert mock_detect.call_count == 2
