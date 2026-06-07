from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from imagine_mcp.errors import ProviderUnsupportedError
from imagine_mcp.providers import grok as provider


@pytest.fixture
def mock_media_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock get_ssrf_safe_client to avoid real network calls."""
    mock_resp = MagicMock()
    mock_resp.content = b"fake-image-bytes"
    mock_resp.headers = {"content-type": "image/png"}

    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    monkeypatch.setattr(provider, "get_ssrf_safe_client", lambda: mock_client)


def test_understand_video_raises() -> None:
    with pytest.raises(ProviderUnsupportedError):
        provider.understand_video("https://example.com/x.mp4", "describe", "poor")


def test_understand_image_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = MagicMock()
    msg = MagicMock()
    msg.content = "a parrot"
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    fake_client.chat.completions.create.return_value = resp
    monkeypatch.setattr(provider, "_openai_compat_client", lambda: fake_client)

    result = provider.understand_image(
        url="https://example.com/parrot.png", prompt="describe", tier="rich"
    )
    assert result["text"] == "a parrot"
    assert result["model"] == "grok-4.20-0309-reasoning"
    assert result["provider"] == "grok"


def test_generate_video_submit(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "fake-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "job-123", "eta_seconds": 45}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp

    monkeypatch.setattr(provider, "get_ssrf_safe_client", lambda: mock_client)

    result = provider.generate_video(prompt="a sunset", tier="poor")
    assert result["job_id"] == "job-123"
    assert result["status"] == "pending"
    assert result["model"] == "grok-imagine-video"


def test_generate_video_poll_done(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "fake-key")
    monkeypatch.setattr("platformdirs.user_cache_dir", lambda _: str(tmp_path))

    mock_poll_resp = MagicMock()
    mock_poll_resp.status_code = 200
    mock_poll_resp.json.return_value = {
        "status": "done",
        "video_url": "https://example.com/video.mp4",
    }

    mock_video_resp = MagicMock()
    mock_video_resp.status_code = 200
    mock_video_resp.content = b"fake-video-bytes"

    mock_client = MagicMock()
    mock_client.get.side_effect = [mock_poll_resp, mock_video_resp]

    monkeypatch.setattr(provider, "get_ssrf_safe_client", lambda: mock_client)

    result = provider.generate_video(prompt="a sunset", tier="poor", job_id="job-123")
    assert result["job_id"] == "job-123"
    assert result["status"] == "done"
    assert result["video_url"] == "https://example.com/video.mp4"
    assert "video_path" in result
    assert Path(result["video_path"]).exists()
