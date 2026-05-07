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
    resp = MagicMock()
    resp.output_text = "a parrot"
    fake_client.responses.create.return_value = resp
    monkeypatch.setattr(provider, "_openai_compat_client", lambda: fake_client)

    result = provider.understand_image(
        url="https://example.com/parrot.png", prompt="describe", tier="rich"
    )
    assert result["text"] == "a parrot"
    assert result["model"] == "grok-3-vision"
    assert result["provider"] == "grok"
