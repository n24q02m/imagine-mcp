from __future__ import annotations

import base64
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

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: mock_client)


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


def test_video_status_calls_generate_video(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_gen = MagicMock(return_value={"status": "done"})
    monkeypatch.setattr(provider, "generate_video", mock_gen)

    result = provider.video_status("rich", "job123")
    assert result == {"status": "done"}
    mock_gen.assert_called_once_with(prompt="", tier="rich", job_id="job123")


def test_edit_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client = MagicMock()

    # Mock GET for initial image download
    mock_resp_get = MagicMock()
    mock_resp_get.content = b"initial-image"
    mock_resp_get.headers = {"content-type": "image/png"}

    # Mock POST for edit request
    mock_resp_post = MagicMock()
    mock_resp_post.status_code = 200
    mock_resp_post.json.return_value = {
        "data": [{"b64_json": base64.b64encode(b"edited-image").decode()}]
    }

    mock_client.get.return_value = mock_resp_get
    mock_client.post.return_value = mock_resp_post

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: mock_client)
    monkeypatch.setattr(provider, "_api_key", lambda: "fake-key")

    result = provider.edit(
        tier="poor", image_url="https://example.com/in.png", prompt="make it blue"
    )
    assert "image_path" in result
    assert result["image_base64"] == base64.b64encode(b"edited-image").decode()
    assert result["model"] == "grok-imagine-image"
