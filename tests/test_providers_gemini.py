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


def test_generate_image_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()

    # Mocking resp.candidates[0].content.parts
    mock_part = MagicMock()
    mock_part.inline_data.data = b"fake-gen-image"
    fake_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]

    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    # Mock Path methods to avoid real file IO
    from pathlib import Path

    monkeypatch.setattr(Path, "write_bytes", MagicMock())
    monkeypatch.setattr(Path, "mkdir", MagicMock())

    result = gemini.generate_image(prompt="a sunset", tier="poor")
    assert "image_path" in result
    assert result["image_base64"] == "ZmFrZS1nZW4taW1hZ2U="  # b64 of b"fake-gen-image"
    assert result["model"] == "gemini-3.1-flash-image-preview"


def test_generate_video_init_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_op = MagicMock()
    fake_op.name = "job-123"
    fake_client.models.generate_videos.return_value = fake_op
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    result = gemini.generate_video(prompt="a cat dancing", tier="poor")
    assert result["job_id"] == "job-123"
    assert result["status"] == "pending"
    assert result["model"] == "veo-3.1-lite-generate-preview"


def test_generate_video_polling_pending_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_op = MagicMock()
    fake_op.done = False
    fake_client.operations.get.return_value = fake_op
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    result = gemini.generate_video(prompt="", tier="poor", job_id="job-123")
    assert result["job_id"] == "job-123"
    assert result["status"] == "pending"


def test_generate_video_polling_success_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_op = MagicMock()
    fake_op.done = True
    fake_op.error = None

    mock_video = MagicMock()
    fake_op.response.generated_videos = [mock_video]

    fake_client.operations.get.return_value = fake_op
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    # Mock Path.mkdir and video.video.save
    from pathlib import Path

    monkeypatch.setattr(Path, "mkdir", MagicMock())

    result = gemini.generate_video(prompt="", tier="poor", job_id="job-123")
    assert result["status"] == "done"
    assert "video_path" in result
    mock_video.video.save.assert_called_once()


def test_generate_video_polling_error_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_op = MagicMock()
    fake_op.done = True
    fake_op.error = "something went wrong"
    fake_client.operations.get.return_value = fake_op
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    from imagine_mcp.errors import ProviderAPIError

    with pytest.raises(
        ProviderAPIError, match="Gemini job error: something went wrong"
    ):
        gemini.generate_video(prompt="", tier="poor", job_id="job-123")
