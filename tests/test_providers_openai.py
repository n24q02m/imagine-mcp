from __future__ import annotations
import io
import base64
from unittest.mock import MagicMock, patch
import pytest
from PIL import Image
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

def test_edit_logic(monkeypatch):
    # Mock client
    fake_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.data = [MagicMock(b64_json=base64.b64encode(b"new_image").decode())]
    fake_client.images.edit.return_value = mock_resp
    monkeypatch.setattr(provider, "_client", lambda: fake_client)

    # Mock media.get_ssrf_safe_client
    with patch("imagine_mcp.media.get_ssrf_safe_client") as mock_get_client:
        mock_http = MagicMock()
        # Create a real small PNG for PIL to open
        img = Image.new('RGB', (100, 100), color='red')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        mock_http.get.return_value.content = buf.getvalue()
        mock_get_client.return_value = mock_http

        result = provider.edit(
            tier="rich",
            image_url="https://example.com/fox.png",
            prompt="add a hat"
        )

        assert result["model"] == "dall-e-2"
        assert result["provider"] == "openai"
        assert "image_path" in result

        # Verify edit call
        args, kwargs = fake_client.images.edit.call_args
        assert kwargs["model"] == "dall-e-2"
        assert kwargs["size"] == "1024x1024"
        assert kwargs["response_format"] == "b64_json"

def test_generate_image_routes_to_edit(monkeypatch):
    # Mock the edit function itself
    mock_edit = MagicMock(return_value={"status": "edited"})
    monkeypatch.setattr(provider, "edit", mock_edit)

    result = provider.generate_image(
        prompt="add a hat",
        tier="rich",
        reference_image_url="https://example.com/fox.png"
    )

    assert result == {"status": "edited"}
    mock_edit.assert_called_once_with("rich", "https://example.com/fox.png", "add a hat")

def test_video_status_raises_unsupported():
    with pytest.raises(ProviderUnsupportedError) as exc:
        provider.video_status("poor", "job-123")
    assert "video_status" in str(exc.value).lower()
