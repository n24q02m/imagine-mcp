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


def test_generate_image_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"url": "https://example.com/flux.png"}]
    }

    def mock_get_ssrf_safe_client():
        c = MagicMock()
        c.post.return_value = mock_resp
        c.get.return_value = MagicMock(content=b"fake-bytes")
        return c

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", mock_get_ssrf_safe_client)
    monkeypatch.setattr(provider, "_api_key", lambda: "fake-key")

    result = provider.generate_image(prompt="a sunset", tier="poor")
    assert result["model"] == "flux-schnell"
    assert "image_path" in result
    assert result["provider"] == "grok"


def test_generate_image_edit_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "url": "https://example.com/flux-edit.png"
    }

    def mock_get_ssrf_safe_client():
        c = MagicMock()
        c.post.return_value = mock_resp
        # GET for the reference image and then GET for the generated image
        c.get.return_value = MagicMock(content=b"fake-bytes")
        return c

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", mock_get_ssrf_safe_client)
    monkeypatch.setattr(provider, "_api_key", lambda: "fake-key")

    result = provider.generate_image(
        prompt="make it blue",
        tier="rich",
        reference_image_url="https://example.com/orig.png"
    )
    assert result["model"] == "flux-pro"
    assert "image_path" in result
    assert result["provider"] == "grok"
