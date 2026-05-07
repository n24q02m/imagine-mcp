from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch

import pytest

from imagine_mcp.errors import ProviderUnsupportedError
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


def test_video_status_pending(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {"status": "pending", "eta_seconds": 10}

    with patch("httpx.get", return_value=fake_resp):
        monkeypatch.setattr(provider, "_api_key", lambda: "fake-key")
        result = provider.video_status("poor", "job-123")
        assert result["status"] == "pending"
        assert result["job_id"] == "job-123"


def test_edit_image_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_img_resp = MagicMock()
    fake_img_resp.status_code = 200
    fake_img_resp.content = b"fake-image-content"

    fake_edit_resp = MagicMock()
    fake_edit_resp.status_code = 200
    fake_edit_resp.json.return_value = {
        "data": [{"b64_json": base64.b64encode(b"edited-image").decode()}]
    }

    mock_ssrf_client = MagicMock()
    mock_ssrf_client.get.return_value = fake_img_resp

    with patch("httpx.post", return_value=fake_edit_resp), patch(
        "imagine_mcp.media.get_ssrf_safe_client", return_value=mock_ssrf_client
    ):
        monkeypatch.setattr(provider, "_api_key", lambda: "fake-key")
        result = provider.edit("rich", "https://example.com/orig.png", "add a hat")
        assert "image_path" in result
        assert result["model"] == "grok-imagine-image-pro"
