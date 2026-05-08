from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

from imagine_mcp.providers import gemini


def test_understand_image_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.text = "a cat on a mat"
    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)
    monkeypatch.setattr(gemini, "_fetch_media_bytes", lambda _: b"fake_bytes")

    result = gemini.understand_image(
        url="https://example.com/cat.png", prompt="describe", tier="poor"
    )
    assert result["text"] == "a cat on a mat"
    assert result["model"] == "gemini-3.1-flash-lite-preview"
    assert result["provider"] == "gemini"
    assert result["tier"] == "poor"


def test_understand_video_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.text = "a cat jumping"
    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)
    monkeypatch.setattr(gemini, "_fetch_media_bytes", lambda _: b"fake_bytes")

    result = gemini.understand_video(
        url="https://example.com/cat.mp4", prompt="describe", tier="rich"
    )
    assert result["text"] == "a cat jumping"
    assert result["model"] == "gemini-3.1-pro-preview"


@pytest.mark.live
def test_understand_image_live() -> None:
    """Live test against real Gemini API."""
    if not os.environ.get("GEMINI_API_KEY"):
        pytest.skip("Requires GEMINI_API_KEY")

    gemini._reset_client()
    result = gemini.understand_image(
        url=(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/"
            "Cat_November_2010-1a.jpg/300px-Cat_November_2010-1a.jpg"
        ),
        prompt="What animal is in this image? Answer in one word.",
        tier="poor",
    )
    assert "cat" in result["text"].lower()


def test_edit_implementation(monkeypatch, tmp_path):
    fake_client = MagicMock()
    fake_resp = MagicMock()
    fake_part = MagicMock()
    fake_part.inline_data.data = b"fake_image_bytes"
    fake_resp.candidates = [MagicMock(content=MagicMock(parts=[fake_part]))]
    fake_client.models.generate_content.return_value = fake_resp

    monkeypatch.setattr(gemini, "_client", lambda: fake_client)
    monkeypatch.setattr(gemini, "_fetch_media_bytes", lambda _: b"fake_bytes")
    monkeypatch.setattr("platformdirs.user_cache_dir", lambda _: str(tmp_path))

    # 1. Test generate_image with reference_image_url
    res = gemini.generate_image(
        prompt="make it blue",
        tier="poor",
        reference_image_url="http://example.com/img.png",
        aspect_ratio="16:9",
    )

    assert "image_path" in res
    assert res["provider"] == "gemini"

    # Verify generate_content call
    _, kwargs = fake_client.models.generate_content.call_args
    assert kwargs["model"] == "gemini-3.1-flash-image-preview"
    assert len(kwargs["contents"]) == 2
    assert kwargs["config"].response_modalities == ["IMAGE"]
    assert kwargs["config"].image_config.aspect_ratio == "16:9"

    # 2. Test edit function
    res_edit = gemini.edit(
        tier="poor", image_url="http://example.com/img.png", prompt="make it blue"
    )
    assert "image_path" in res_edit
    assert res_edit["provider"] == "gemini"


def test_video_status(monkeypatch):
    fake_client = MagicMock()
    fake_op = MagicMock()
    fake_op.done = False
    fake_client.operations.get.return_value = fake_op

    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    res = gemini.video_status(tier="poor", job_id="job123")
    assert res["status"] == "pending"
    assert res["job_id"] == "job123"
