from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

from imagine_mcp.providers import gemini


@pytest.fixture
def mock_media_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock get_ssrf_safe_client and download_to_path to avoid real network calls."""
    mock_resp = MagicMock()
    mock_resp.content = b"fake-image-bytes"
    mock_resp.headers = {"content-type": "image/png"}

    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: mock_client)
    monkeypatch.setattr("imagine_mcp.media.download_to_path", lambda url, dest: dest)


def test_understand_image_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
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


def test_understand_video_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
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


def test_understand_multimodal_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.text = "mixed content description"
    fake_client.models.generate_content.return_value = fake_response
    fake_client.files.upload.return_value = MagicMock(name="fake_gfile")
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    # Mock detect_media_type to return image for .png and video for .mp4
    def mock_detect(url):
        return "video" if url.endswith(".mp4") else "image"

    monkeypatch.setattr("imagine_mcp.media.detect_media_type", mock_detect)

    result = gemini.understand_multimodal(
        urls=["https://example.com/a.png", "https://example.com/b.mp4"],
        prompt="describe both",
        tier="rich",
    )
    assert result["text"] == "mixed content description"
    assert result["multimodal"] is True
    assert result["tier"] == "rich"
    assert fake_client.files.upload.called


def test_understand_multimodal_with_media_types_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.text = "optimized mixed content description"
    fake_client.models.generate_content.return_value = fake_response
    fake_client.files.upload.return_value = MagicMock(name="fake_gfile")
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    # We don't mock detect_media_type here to ensure it's NOT called
    mock_detect = MagicMock()
    monkeypatch.setattr("imagine_mcp.media.detect_media_type", mock_detect)

    result = gemini.understand_multimodal(
        urls=["https://example.com/a.png", "https://example.com/b.mp4"],
        prompt="describe both",
        tier="rich",
        media_types=["image", "video"],
    )
    assert result["text"] == "optimized mixed content description"
    assert not mock_detect.called
    assert fake_client.files.upload.called
