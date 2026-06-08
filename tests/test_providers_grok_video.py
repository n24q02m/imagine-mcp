from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from imagine_mcp.providers import grok as provider


@pytest.fixture
def mock_deps(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    monkeypatch.setattr(provider, "_api_key", lambda: "fake-key")

    mock_client = MagicMock()
    # Mocking get_ssrf_safe_client to return our mock_client
    monkeypatch.setattr(
        "imagine_mcp.providers.grok.get_ssrf_safe_client", lambda: mock_client
    )
    return mock_client


def test_generate_video_submit(mock_deps: MagicMock) -> None:
    # Mock submission response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "job123", "eta_seconds": 45}
    mock_deps.post.return_value = mock_resp

    result = provider.generate_video(
        prompt="a flying cat",
        tier="rich",
    )

    assert result["job_id"] == "job123"
    assert result["status"] == "pending"
    assert result["eta_seconds"] == 45
    assert result["provider"] == "grok"


def test_generate_video_poll_pending(mock_deps: MagicMock) -> None:
    # Mock polling response (pending)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "pending", "eta_seconds": 10}
    mock_deps.get.return_value = mock_resp

    result = provider.generate_video(
        prompt="a flying cat", tier="rich", job_id="job123"
    )

    assert result["job_id"] == "job123"
    assert result["status"] == "pending"
    assert result["eta_seconds"] == 10


def test_generate_video_poll_done(mock_deps: MagicMock) -> None:
    # Mock polling response (done)
    mock_poll_resp = MagicMock()
    mock_poll_resp.status_code = 200
    mock_poll_resp.json.return_value = {
        "status": "done",
        "video_url": "https://example.com/video.mp4",
    }

    mock_video_resp = MagicMock()
    mock_video_resp.content = b"fake-video-bytes"

    # Configure mock_deps.get to return different responses based on call
    mock_deps.get.side_effect = [mock_poll_resp, mock_video_resp]

    result = provider.generate_video(
        prompt="a flying cat", tier="rich", job_id="job123"
    )

    assert result["job_id"] == "job123"
    assert result["status"] == "done"
    assert "video_path" in result
    assert result["video_url"] == "https://example.com/video.mp4"
