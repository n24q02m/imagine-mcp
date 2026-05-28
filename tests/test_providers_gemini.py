from __future__ import annotations

import base64
import os
from pathlib import Path
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


def test_generate_image_mocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_part = MagicMock()
    fake_part.inline_data.data = b"fake-generated-image"
    fake_response.candidates = [MagicMock()]
    fake_response.candidates[0].content.parts = [fake_part]
    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)
    monkeypatch.setattr("platformdirs.user_cache_dir", lambda _: str(tmp_path))

    result = gemini.generate_image(prompt="a sunset", tier="poor")

    assert "fake-generated-image" in base64.b64decode(result["image_base64"]).decode()
    assert result["model"] == "gemini-3.1-flash-image-preview"
    assert result["provider"] == "gemini"
    assert result["tier"] == "poor"
    assert Path(result["image_path"]).exists()


def test_generate_image_with_reference_mocked(
    mock_media_fetch: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_part = MagicMock()
    fake_part.inline_data.data = b"fake-generated-image-ref"
    fake_response.candidates = [MagicMock()]
    fake_response.candidates[0].content.parts = [fake_part]
    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)
    monkeypatch.setattr("platformdirs.user_cache_dir", lambda _: str(tmp_path))

    result = gemini.generate_image(
        prompt="a sunset like this",
        tier="rich",
        reference_image_url="https://example.com/ref.png",
    )

    assert (
        "fake-generated-image-ref" in base64.b64decode(result["image_base64"]).decode()
    )
    assert result["model"] == "gemini-3-pro-image-preview"
    assert result["provider"] == "gemini"
    assert result["tier"] == "rich"
    assert Path(result["image_path"]).exists()


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
