from __future__ import annotations

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
    with pytest.raises(ProviderUnsupportedError):
        provider.understand_video("https://example.com/x.mp4", "describe", "poor")


def test_generate_video_raises() -> None:
    with pytest.raises(ProviderUnsupportedError):
        provider.generate_video("a dog", "poor")


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


def test_generate_image_gpt_poor(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.data = [MagicMock(b64_json="ZmFrZS1iNjQtZGF0YQ==")]  # "fake-b64-data"
    fake_client.images.generate.return_value = fake_response
    monkeypatch.setattr(provider, "_client", lambda: fake_client)

    # Mock get_model_id to return a GPT model
    monkeypatch.setattr(
        "imagine_mcp.providers.openai.get_model_id",
        lambda p, a, m, t: "gpt-image-1-mini",
    )

    result = provider.generate_image(prompt="a cat", tier="poor", aspect_ratio="1:1")

    fake_client.images.generate.assert_called_once_with(
        model="gpt-image-1-mini",
        prompt="a cat",
        size="1024x1024",
        quality="low",
        n=1,
    )
    assert result["image_base64"] == "ZmFrZS1iNjQtZGF0YQ=="


def test_generate_image_gpt_rich_16_9(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.data = [MagicMock(b64_json="ZmFrZS1iNjQtZGF0YQ==")]
    fake_client.images.generate.return_value = fake_response
    monkeypatch.setattr(provider, "_client", lambda: fake_client)

    monkeypatch.setattr(
        "imagine_mcp.providers.openai.get_model_id", lambda p, a, m, t: "gpt-image-1.5"
    )

    provider.generate_image(prompt="a dog", tier="rich", aspect_ratio="16:9")

    fake_client.images.generate.assert_called_once_with(
        model="gpt-image-1.5",
        prompt="a dog",
        size="1536x1024",
        quality="high",
        n=1,
    )


def test_generate_image_dalle_rich_16_9(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.data = [MagicMock(b64_json="ZmFrZS1iNjQtZGF0YQ==")]
    fake_client.images.generate.return_value = fake_response
    monkeypatch.setattr(provider, "_client", lambda: fake_client)

    monkeypatch.setattr(
        "imagine_mcp.providers.openai.get_model_id", lambda p, a, m, t: "dall-e-3"
    )

    provider.generate_image(prompt="a bird", tier="rich", aspect_ratio="16:9")

    fake_client.images.generate.assert_called_once_with(
        model="dall-e-3",
        prompt="a bird",
        size="1792x1024",
        quality="hd",
        response_format="b64_json",
        n=1,
    )


def test_generate_image_gpt_edit(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.data = [MagicMock(b64_json="ZmFrZS1iNjQtZGF0YQ==")]
    fake_client.images.edit.return_value = fake_response
    monkeypatch.setattr(provider, "_client", lambda: fake_client)

    monkeypatch.setattr(
        "imagine_mcp.providers.openai.get_model_id", lambda p, a, m, t: "gpt-image-1.5"
    )

    provider.generate_image(
        prompt="make it blue",
        tier="rich",
        reference_image_url="https://example.com/img.png",
        aspect_ratio="9:16",
    )

    fake_client.images.edit.assert_called_once_with(
        model="gpt-image-1.5",
        image=b"fake-image-bytes",
        prompt="make it blue",
        size="1024x1536",
        quality="high",
    )
