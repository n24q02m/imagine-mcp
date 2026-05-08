from __future__ import annotations

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
    fake_client = MagicMock()
    fake_msg = MagicMock()
    fake_msg.content = "a dog"
    fake_choice = MagicMock()
    fake_choice.message = fake_msg
    fake_resp = MagicMock()
    fake_resp.choices = [fake_choice]
    fake_client.chat.completions.create.return_value = fake_resp

    monkeypatch.setattr(provider, "_client", lambda: fake_client)

    result = provider.understand_image(
        url="https://example.com/dog.png", prompt="describe", tier="poor"
    )
    assert result["text"] == "a dog"
    assert result["model"] == "gpt-5.4-mini"
    assert result["provider"] == "openai"
