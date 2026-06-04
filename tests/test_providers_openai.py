from __future__ import annotations

import base64
from unittest.mock import MagicMock

import pytest

from imagine_mcp.errors import ProviderUnsupportedError
from imagine_mcp.providers import openai as provider


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
    with pytest.raises(
        ProviderUnsupportedError, match=r"GPT-5\.4 vision is image-only"
    ):
        provider.understand_video("https://example.com/x.mp4", "describe", "poor")


def test_generate_video_raises() -> None:
    with pytest.raises(ProviderUnsupportedError, match=r"Sora 2 API shutdown"):
        provider.generate_video("a dog", "poor")


def test_video_status_raises() -> None:
    with pytest.raises(ProviderUnsupportedError, match=r"Sora 2 API shutdown"):
        provider.video_status("job-123", "a dog", "poor")


def test_understand_image_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = MagicMock()
    fake.responses.create.return_value = MagicMock(output_text="a dog")
    monkeypatch.setattr(provider, "_client", lambda: fake)

    result = provider.understand_image(
        url="https://example.com/dog.png", prompt="describe", tier="poor"
    )
    assert result["text"] == "a dog"
    assert result["model"] == "gpt-5.4-mini"
    assert result["provider"] == "openai"


def test_edit_mocked(mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = MagicMock()
    fake_img = MagicMock()
    fake_img.b64_json = base64.b64encode(b"fake-edited-image").decode()
    fake.images.edit.return_value = MagicMock(data=[fake_img])
    monkeypatch.setattr(provider, "_client", lambda: fake)

    result = provider.edit(
        url="https://example.com/dog.png", prompt="make it a cat", tier="poor"
    )
    assert "image_path" in result
    assert result["model"] == "gpt-image-1-mini"
    assert result["provider"] == "openai"


def test_generate_image_delegates_to_edit(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Use a spy or mock to verify edit is called
    mock_edit = MagicMock(return_value={"status": "edited"})
    monkeypatch.setattr(provider, "edit", mock_edit)

    result = provider.generate_image(
        prompt="make it a cat",
        tier="poor",
        reference_image_url="https://example.com/dog.png",
    )
    assert result == {"status": "edited"}
    mock_edit.assert_called_once_with(
        "https://example.com/dog.png", "make it a cat", "poor", "1:1"
    )
