from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from imagine_mcp.errors import ProviderAPIError, ProviderUnsupportedError
from imagine_mcp.providers import grok as provider


def test_understand_video_raises() -> None:
    with pytest.raises(ProviderUnsupportedError):
        provider.understand_video("https://example.com/x.mp4", "describe", "poor")


def test_understand_image_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_edit_delegates_to_generate_image() -> None:
    with patch("imagine_mcp.providers.grok.generate_image") as mock_gen:
        mock_gen.return_value = {"status": "ok"}
        result = provider.edit("rich", "https://example.com/img.png", "make it blue")
        assert result == {"status": "ok"}
        mock_gen.assert_called_once_with(
            "make it blue", "rich", reference_image_url="https://example.com/img.png"
        )


def test_video_status_pending(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XAI_API_KEY", "test-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "pending", "progress": 42}

    with patch("httpx.get", return_value=mock_resp):
        result = provider.video_status("poor", "job-123")
        assert result["status"] == "pending"
        assert result["job_id"] == "job-123"
        assert result["progress"] == 42


def test_video_status_done(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XAI_API_KEY", "test-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "done",
        "video": {"url": "https://example.com/vid.mp4"},
    }

    mock_media_client = MagicMock()
    mock_media_client.get.return_value.content = b"fake-video-bytes"

    with (
        patch("httpx.get", return_value=mock_resp),
        patch("imagine_mcp.media.get_ssrf_safe_client", return_value=mock_media_client),
        patch("pathlib.Path.write_bytes") as mock_write,
    ):
        result = provider.video_status("rich", "job-123")
        assert result["status"] == "done"
        assert result["video_url"] == "https://example.com/vid.mp4"
        assert "video_path" in result
        mock_write.assert_called_once_with(b"fake-video-bytes")


def test_video_status_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XAI_API_KEY", "test-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "failed", "error": {"message": "oops"}}

    with patch("httpx.get", return_value=mock_resp):
        with pytest.raises(ProviderAPIError) as exc:
            provider.video_status("poor", "job-123")
        assert "oops" in str(exc.value)


def test_generate_video_submission(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XAI_API_KEY", "test-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"request_id": "req-456"}

    with patch("httpx.post", return_value=mock_resp) as mock_post:
        result = provider.generate_video("a flying pig", "poor")
        assert result["job_id"] == "req-456"
        assert result["status"] == "pending"

        # Verify payload fields match documentation
        _args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["prompt"] == "a flying pig"
        assert payload["duration"] == 8
        assert payload["aspect_ratio"] == "16:9"
