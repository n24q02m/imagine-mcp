from __future__ import annotations

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


def test_grok_edit_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_gen = MagicMock(return_value={"status": "done"})
    monkeypatch.setattr(provider, "generate_image", mock_gen)

    result = provider.edit(
        tier="poor", image_url="http://img.png", prompt="make it blue"
    )
    assert result == {"status": "done"}
    mock_gen.assert_called_once_with(
        prompt="make it blue", tier="poor", reference_image_url="http://img.png"
    )


def test_grok_video_status_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_gen = MagicMock(return_value={"status": "done"})
    monkeypatch.setattr(provider, "generate_video", mock_gen)

    result = provider.video_status(tier="rich", job_id="job-123")
    assert result == {"status": "done"}
    mock_gen.assert_called_once_with(prompt="", tier="rich", job_id="job-123")
