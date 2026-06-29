from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock

import pytest

from imagine_mcp.errors import ProviderAPIError, ProviderUnsupportedError
from imagine_mcp.providers import grok as provider


@pytest.fixture
def mock_media(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Mock async media fetchers and emit_media."""
    mock_client = AsyncMock()
    monkeypatch.setattr(
        "imagine_mcp.providers.grok.get_ssrf_safe_async_client", lambda: mock_client
    )

    mock_emit = AsyncMock(return_value={"image_base64": "fake-b64"})
    monkeypatch.setattr("imagine_mcp.media.emit_media", mock_emit)

    return mock_client


@pytest.mark.asyncio
async def test_understand_video_raises() -> None:
    with pytest.raises(ProviderUnsupportedError):
        await provider.understand_video("https://example.com/x.mp4", "describe", "poor")


@pytest.mark.asyncio
async def test_understand_image_mocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # understand_image uses mcp_core.llm.acompletion
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "a parrot"

    mock_client = AsyncMock()
    mock_client.get.return_value = MagicMock(
        content=b"fake-bytes", headers={"content-type": "image/png"}
    )
    monkeypatch.setattr(
        "imagine_mcp.providers.grok.get_ssrf_safe_async_client", lambda: mock_client
    )

    captured: dict[str, object] = {}

    async def fake_acompletion(**kwargs: object) -> object:
        captured.update(kwargs)
        return mock_resp

    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    monkeypatch.setattr("mcp_core.llm.acompletion", fake_acompletion)

    result = await provider.understand_image(
        url="https://example.com/parrot.png", prompt="describe", tier="rich"
    )
    assert result["text"] == "a parrot"
    assert captured["api_key"] == "xai-test"


@pytest.mark.asyncio
async def test_generate_image_b64(
    mock_media: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"b64_json": base64.b64encode(b"gen-image-bytes").decode()}]
    }
    mock_media.post.return_value = mock_resp

    result = await provider.generate_image(prompt="a sunset", tier="poor")

    assert result["image_base64"] == "fake-b64"
    assert result["model"] == "grok-imagine-image"

    # Verify POST call
    args, kwargs = mock_media.post.call_args
    assert args[0].endswith("/images/generations")
    assert kwargs["json"]["prompt"] == "a sunset"
    assert kwargs["headers"]["Authorization"] == "Bearer xai-test"


@pytest.mark.asyncio
async def test_generate_image_url(
    mock_media: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    # First call: POST returns URL
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post_resp.json.return_value = {
        "data": [{"url": "https://example.com/generated.png"}]
    }
    mock_media.post.return_value = mock_post_resp

    # Second call: GET fetches the URL
    mock_get_resp = MagicMock()
    mock_get_resp.content = b"fetched-image-bytes"
    mock_media.get.return_value = mock_get_resp

    result = await provider.generate_image(prompt="a sunset", tier="rich")

    assert result["image_base64"] == "fake-b64"
    assert result["model"] == "grok-imagine-image-pro"
    assert mock_media.get.called
    assert mock_media.get.call_args[0][0] == "https://example.com/generated.png"


@pytest.mark.asyncio
async def test_generate_image_with_reference(
    mock_media: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    # Mock download of reference image
    mock_ref_resp = MagicMock()
    mock_ref_resp.content = b"ref-bytes"
    mock_ref_resp.headers = {"content-type": "image/jpeg"}

    # Mock API response
    mock_api_resp = MagicMock()
    mock_api_resp.status_code = 200
    mock_api_resp.json.return_value = {
        "data": [{"b64_json": base64.b64encode(b"gen-bytes").decode()}]
    }

    # Sequential returns for GET (ref) then POST (gen)
    mock_media.get.return_value = mock_ref_resp
    mock_media.post.return_value = mock_api_resp

    await provider.generate_image(
        prompt="like this",
        tier="poor",
        reference_image_url="https://example.com/ref.jpg",
    )

    # Check if reference image was downloaded
    mock_media.get.assert_called_with(
        "https://example.com/ref.jpg", follow_redirects=True, timeout=60
    )

    # Check if POST payload contains reference_image
    kwargs = mock_media.post.call_args[1]
    assert "reference_image" in kwargs["json"]
    assert kwargs["json"]["reference_image"].startswith("data:image/jpeg;base64,")


@pytest.mark.asyncio
async def test_generate_image_error(
    mock_media: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "Bad Prompt"
    mock_media.post.return_value = mock_resp

    with pytest.raises(
        ProviderAPIError, match="Grok image generate failed: Bad Prompt"
    ):
        await provider.generate_image(prompt="invalid", tier="poor")


@pytest.mark.asyncio
async def test_generate_video_submit(
    mock_media: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "job-123", "eta_seconds": 30}
    mock_media.post.return_value = mock_resp

    result = await provider.generate_video(prompt="a dancing cat", tier="poor")

    assert result["job_id"] == "job-123"
    assert result["status"] == "pending"
    assert result["model"] == "grok-imagine-video"

    # Verify POST payload
    kwargs = mock_media.post.call_args[1]
    assert kwargs["json"]["prompt"] == "a dancing cat"
    assert kwargs["json"]["duration_seconds"] == 8


@pytest.mark.asyncio
async def test_generate_video_poll_pending(
    mock_media: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "pending", "eta_seconds": 10}
    mock_media.get.return_value = mock_resp

    result = await provider.generate_video(prompt="", tier="poor", job_id="job-123")

    assert result["job_id"] == "job-123"
    assert result["status"] == "pending"
    assert result["eta_seconds"] == 10

    # Verify GET URL (quoted)
    args = mock_media.get.call_args[0]
    assert args[0].endswith("/videos/generations/job-123")


@pytest.mark.asyncio
async def test_generate_video_poll_done(
    mock_media: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    # Mock polling response
    mock_poll_resp = MagicMock()
    mock_poll_resp.status_code = 200
    mock_poll_resp.json.return_value = {
        "status": "done",
        "video_url": "https://example.com/result.mp4",
    }

    # Mock video download
    mock_video_resp = MagicMock()
    mock_video_resp.content = b"mp4-bytes"

    mock_media.get.side_effect = [mock_poll_resp, mock_video_resp]

    # Mock emit_media for video
    monkeypatch.setattr(
        "imagine_mcp.media.emit_media",
        AsyncMock(return_value={"video_base64": "fake-video-b64"}),
    )

    result = await provider.generate_video(prompt="", tier="poor", job_id="job-123")

    assert result["status"] == "done"
    assert result["video_base64"] == "fake-video-b64"
    assert result["video_url"] == "https://example.com/result.mp4"


@pytest.mark.asyncio
async def test_generate_video_poll_failed(
    mock_media: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "failed", "error": "Safety violation"}
    mock_media.get.return_value = mock_resp

    with pytest.raises(
        ProviderAPIError, match="Grok video generation failed: Safety violation"
    ):
        await provider.generate_video(prompt="", tier="poor", job_id="job-123")


@pytest.mark.asyncio
async def test_generate_video_with_reference(
    mock_media: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    # Mock download of reference image
    mock_ref_resp = MagicMock()
    mock_ref_resp.content = b"ref-bytes"
    mock_ref_resp.headers = {"content-type": "image/jpeg"}

    # Mock API response for submission
    mock_api_resp = MagicMock()
    mock_api_resp.status_code = 200
    mock_api_resp.json.return_value = {"id": "job-123"}

    # Sequential returns for GET (ref) then POST (gen)
    mock_media.get.return_value = mock_ref_resp
    mock_media.post.return_value = mock_api_resp

    await provider.generate_video(
        prompt="like this",
        tier="poor",
        reference_image_url="https://example.com/ref.jpg",
    )

    # Check if reference image was downloaded
    mock_media.get.assert_called_with(
        "https://example.com/ref.jpg", follow_redirects=True, timeout=60
    )

    # Check if POST payload contains source_image
    kwargs = mock_media.post.call_args[1]
    assert "source_image" in kwargs["json"]
    assert kwargs["json"]["source_image"].startswith("data:image/jpeg;base64,")


@pytest.mark.asyncio
async def test_generate_video_submit_error(
    mock_media: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    mock_media.post.return_value = mock_resp

    with pytest.raises(
        ProviderAPIError, match="Grok video submit failed: Internal Server Error"
    ):
        await provider.generate_video(prompt="a dancing cat", tier="poor")


@pytest.mark.asyncio
async def test_generate_video_poll_error(
    mock_media: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.text = "Not Found"
    mock_media.get.return_value = mock_resp

    with pytest.raises(ProviderAPIError, match="Grok video poll failed: Not Found"):
        await provider.generate_video(prompt="", tier="poor", job_id="job-123")
