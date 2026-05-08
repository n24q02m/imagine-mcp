from __future__ import annotations

from unittest.mock import MagicMock

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
    monkeypatch.setattr(provider, "_client", lambda: fake_client)

    result = provider.understand_image(
        url="https://example.com/parrot.png", prompt="describe", tier="rich"
    )
    assert result["text"] == "a parrot"
    assert result["model"] == "grok-4.20-0309-reasoning"
    assert result["provider"] == "grok"


def test_generate_image_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()

    # Mock response object
    img_obj = MagicMock()
    img_obj.b64_json = "ZmFrZSBiYXNlNjQ="  # "fake base64"
    img_obj.url = None

    resp = MagicMock()
    resp.data = [img_obj]

    fake_client.images.generate.return_value = resp
    monkeypatch.setattr(provider, "_client", lambda: fake_client)

    # Mock file writing to avoid side effects
    monkeypatch.setattr("pathlib.Path.mkdir", MagicMock())
    monkeypatch.setattr("pathlib.Path.write_bytes", MagicMock())

    result = provider.generate_image(
        prompt="a cool image", tier="rich", aspect_ratio="16:9"
    )

    assert result["model"] == "flux-pro"
    assert result["provider"] == "grok"
    assert result["tier"] == "rich"
    assert result["image_base64"] == "ZmFrZSBiYXNlNjQ="

    # Verify extra_body parameters
    _, kwargs = fake_client.images.generate.call_args
    assert kwargs["extra_body"]["aspect_ratio"] == "16:9"
    assert kwargs["extra_body"]["quality"] == "high"


def test_generate_alias_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    img_obj = MagicMock()
    img_obj.b64_json = "YWxpYXM="
    img_obj.url = None
    resp = MagicMock()
    resp.data = [img_obj]
    fake_client.images.generate.return_value = resp
    monkeypatch.setattr(provider, "_client", lambda: fake_client)
    monkeypatch.setattr("pathlib.Path.mkdir", MagicMock())
    monkeypatch.setattr("pathlib.Path.write_bytes", MagicMock())

    # Test the generate(tier, prompt, **kwargs) entry point
    result = provider.generate(tier="poor", prompt="alias test", aspect_ratio="3:2")

    assert result["model"] == "flux-schnell"
    assert result["image_base64"] == "YWxpYXM="
    _, kwargs = fake_client.images.generate.call_args
    assert kwargs["extra_body"]["aspect_ratio"] == "3:2"
