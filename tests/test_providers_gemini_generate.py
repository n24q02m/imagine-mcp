from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from imagine_mcp.errors import ProviderAPIError
from imagine_mcp.providers import gemini
from imagine_mcp.providers.base import ImageParams


def test_generate_image_missing_data(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()

    # Mocking resp.candidates[0].content.parts
    # We'll make it return a part that doesn't have inline_data
    fake_part = MagicMock()
    if hasattr(fake_part, "inline_data"):
        del fake_part.inline_data  # Ensure hasattr(part, "inline_data") is False

    fake_response.candidates = [MagicMock()]
    fake_response.candidates[0].content.parts = [fake_part]

    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    with pytest.raises(ProviderAPIError, match="Gemini returned no image") as exc_info:
        gemini.generate_image(ImageParams(prompt="a sunset", tier="poor"))

    assert exc_info.value.status_code == 500


def test_generate_image_empty_inline_data(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()

    # Mocking resp.candidates[0].content.parts
    # We'll make it return a part that has empty inline_data
    fake_part = MagicMock()
    fake_part.inline_data = None

    fake_response.candidates = [MagicMock()]
    fake_response.candidates[0].content.parts = [fake_part]

    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    with pytest.raises(ProviderAPIError, match="Gemini returned no image") as exc_info:
        gemini.generate_image(ImageParams(prompt="a sunset", tier="poor"))

    assert exc_info.value.status_code == 500
