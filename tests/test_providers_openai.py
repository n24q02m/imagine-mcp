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
    fake = MagicMock()
    # Mock chat.completions.create
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "a dog"
    fake.chat.completions.create.return_value = mock_response

    monkeypatch.setattr(provider, "_client", lambda: fake)

    result = provider.understand_image(
        url="https://example.com/dog.png", prompt="describe", tier="poor"
    )
    assert result["text"] == "a dog"
    assert result["model"] == "gpt-4o-mini"
    assert result["provider"] == "openai"

    # Test rich tier
    result_rich = provider.understand_image(
        url="https://example.com/dog.png", prompt="describe", tier="rich"
    )
    assert result_rich["model"] == "gpt-4o"
