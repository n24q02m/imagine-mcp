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
    if not os.environ.get("GOOGLE_AI_STUDIO_API_KEY"):
        pytest.skip("Requires GOOGLE_AI_STUDIO_API_KEY")

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
