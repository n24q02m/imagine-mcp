from __future__ import annotations

import base64
from unittest.mock import MagicMock

import pytest

from imagine_mcp.errors import ProviderUnsupportedError
from imagine_mcp.providers import openai as provider


def test_understand_video_raises() -> None:
    with pytest.raises(ProviderUnsupportedError):
        provider.understand_video("https://example.com/x.mp4", "describe", "poor")


def test_generate_video_raises() -> None:
    with pytest.raises(ProviderUnsupportedError):
        provider.generate_video("a dog", "poor")


def test_understand_image_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = MagicMock()
    fake.responses.create.return_value = MagicMock(output_text="a dog")
    monkeypatch.setattr(provider, "_client", lambda: fake)

    result = provider.understand_image(
        url="https://example.com/dog.png", prompt="describe", tier="poor"
    )
    assert result["text"] == "a dog"
    assert result["model"] == "gpt-5.4-mini"
    assert result["provider"] == "openai"


def test_generate_image_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = MagicMock()
    fake_data = MagicMock()
    # Mocking b64_json response
    fake_data.b64_json = base64.b64encode(b"fake image").decode()
    fake.images.generate.return_value = MagicMock(data=[fake_data])
    monkeypatch.setattr(provider, "_client", lambda: fake)

    result = provider.generate_image(prompt="a blue dog", tier="poor")

    assert "image_path" in result
    assert result["image_base64"] == fake_data.b64_json
    assert result["model"] == "gpt-image-1-mini"
    assert result["provider"] == "openai"

    # Verify SDK call
    _, kwargs = fake.images.generate.call_args
    assert kwargs["model"] == "gpt-image-1-mini"
    assert kwargs["prompt"] == "a blue dog"
    assert kwargs["response_format"] == "b64_json"


def test_generate_image_edit_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = MagicMock()
    fake_data = MagicMock()
    fake_data.b64_json = base64.b64encode(b"edited image").decode()
    fake.images.edit.return_value = MagicMock(data=[fake_data])
    monkeypatch.setattr(provider, "_client", lambda: fake)

    # Mock SSRF safe client
    fake_ssrf = MagicMock()
    fake_ssrf.get.return_value = MagicMock(content=b"original bytes")
    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: fake_ssrf)

    result = provider.generate_image(
        prompt="add a hat",
        tier="rich",
        reference_image_url="https://example.com/orig.png",
    )

    assert result["image_base64"] == fake_data.b64_json
    assert result["model"] == "gpt-image-1.5"

    # Verify SDK call
    _, kwargs = fake.images.edit.call_args
    assert kwargs["model"] == "gpt-image-1.5"
    assert kwargs["image"] == b"original bytes"
    assert kwargs["prompt"] == "add a hat"
    assert kwargs["response_format"] == "b64_json"
