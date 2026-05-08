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


def test_understand_multimodal_avoids_detect_media_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.text = "multimodal response"
    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    detect_calls = []

    def mock_detect(url: str) -> str:
        detect_calls.append(url)
        return "image"

    monkeypatch.setattr("imagine_mcp.media.detect_media_type", mock_detect)

    # If we pass media_types, detect_media_type should NOT be called
    urls = ["https://example.com/1.png", "https://example.com/2.mp4"]
    media_types = ["image", "video"]

    result = gemini.understand_multimodal(
        urls=urls, prompt="describe both", tier="poor", media_types=media_types
    )

    assert result["text"] == "multimodal response"
    assert len(detect_calls) == 0, (
        "detect_media_type was called despite providing types"
    )

    # Verify parts passed to client
    call_args = fake_client.models.generate_content.call_args
    contents = call_args.kwargs["contents"]
    # parts: [prompt, url1, url2]
    assert len(contents) == 3
    # Check mime types used in Parts
    # We need to see how Parts are constructed in gemini.py
    # parts.append(types.Part.from_uri(file_uri=u, mime_type=mime))
