from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from imagine_mcp.providers import gemini


@pytest.fixture
def mock_media_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock async media fetchers to avoid real network calls."""
    mock_resp = MagicMock()
    mock_resp.content = b"fake-image-bytes"
    mock_resp.headers = {"content-type": "image/png"}

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp

    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )
    monkeypatch.setattr(
        "imagine_mcp.media.download_to_path_async", AsyncMock(return_value=None)
    )


@pytest.mark.asyncio
async def test_understand_video_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock()
    fake_client.aio.files.upload = AsyncMock()

    fake_response = MagicMock()
    fake_response.text = "a cat jumping"
    fake_client.aio.models.generate_content.return_value = fake_response
    fake_client.aio.files.upload.return_value = MagicMock(name="fake_gfile")
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    result = await gemini.understand_video(
        url="https://example.com/cat.mp4",
        prompt="describe",
        model="gemini-3.1-pro-preview",
    )
    assert result["text"] == "a cat jumping"
    assert result["model"] == "gemini-3.1-pro-preview"


@pytest.mark.live
@pytest.mark.asyncio
async def test_understand_image_live() -> None:
    """Live test against real Gemini API (litellm passthrough via dispatcher)."""
    if not os.environ.get("GEMINI_API_KEY"):
        pytest.skip("Requires GEMINI_API_KEY")

    from imagine_mcp.dispatcher import dispatch_understand

    result = await dispatch_understand(
        media_urls=[
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/"
            "Cat_November_2010-1a.jpg/300px-Cat_November_2010-1a.jpg"
        ],
        prompt="What animal is in this image? Answer in one word.",
        provider=None,
        tier="poor",
        model="gemini/gemini-3.1-flash-lite-preview",
    )
    assert "cat" in result["text"].lower()


@pytest.mark.asyncio
async def test_understand_multimodal_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock()
    fake_client.aio.files.upload = AsyncMock()

    fake_response = MagicMock()
    fake_response.text = "mixed content description"
    fake_client.aio.models.generate_content.return_value = fake_response
    fake_client.aio.files.upload.return_value = MagicMock(name="fake_gfile")
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    # Mock detect_media_type_async
    async def mock_detect(url):
        return "video" if url.endswith(".mp4") else "image"

    monkeypatch.setattr("imagine_mcp.media.detect_media_type_async", mock_detect)

    result = await gemini.understand_multimodal(
        urls=["https://example.com/a.png", "https://example.com/b.mp4"],
        prompt="describe both",
        model="gemini-3.1-pro-preview",
    )
    assert result["text"] == "mixed content description"
    assert result["multimodal"] is True
    assert result["model"] == "gemini-3.1-pro-preview"
    assert fake_client.aio.files.upload.called


@pytest.mark.asyncio
async def test_understand_multimodal_with_media_types_mocked(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock()
    fake_client.aio.files.upload = AsyncMock()

    fake_response = MagicMock()
    fake_response.text = "optimized mixed content description"
    fake_client.aio.models.generate_content.return_value = fake_response
    fake_client.aio.files.upload.return_value = MagicMock(name="fake_gfile")
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    # We don't mock detect_media_type_async here to ensure it's NOT called
    mock_detect = AsyncMock()
    monkeypatch.setattr("imagine_mcp.media.detect_media_type_async", mock_detect)

    result = await gemini.understand_multimodal(
        urls=["https://example.com/a.png", "https://example.com/b.mp4"],
        prompt="describe both",
        model="gemini-3.1-pro-preview",
        media_types=["image", "video"],
    )
    assert result["text"] == "optimized mixed content description"
    assert not mock_detect.called
    assert fake_client.aio.files.upload.called


@pytest.mark.asyncio
async def test_understand_multimodal_keeps_url_order_when_probes_finish_out_of_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parts follow URL order even when the first URL resolves last.

    Detection and fetch are pipelined per URL, so the tasks complete in an
    order the caller does not control. Gemini reads ``contents`` positionally,
    so a swap here would silently pair each image with the wrong prompt slot.
    """

    async def fake_get(url: str, **_kwargs: object) -> MagicMock:
        resp = MagicMock()
        resp.content = url.encode()
        resp.headers = {"content-type": "image/png"}
        return resp

    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=fake_get)
    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )

    async def staggered_detect(url: str) -> str:
        # The first URL's probe is the slowest, inverting completion order.
        await asyncio.sleep(0.05 if url.endswith("first.png") else 0.0)
        return "image"

    monkeypatch.setattr("imagine_mcp.media.detect_media_type_async", staggered_detect)

    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock(
        return_value=MagicMock(text="ordered")
    )
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    urls = ["https://example.com/first.png", "https://example.com/second.png"]
    await gemini.understand_multimodal(
        urls=urls, prompt="describe", model="gemini-3.1-pro-preview"
    )

    contents = fake_client.aio.models.generate_content.call_args.kwargs["contents"]
    assert [part.inline_data.data for part in contents[1:]] == [
        url.encode() for url in urls
    ]


@pytest.mark.asyncio
async def test_understand_multimodal_propagates_detect_failure(
    mock_media_fetch: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing probe surfaces as its own exception, not an ExceptionGroup.

    Callers upstream match on the concrete error type, so the TaskGroup's
    group wrapper must not reach them.
    """
    from imagine_mcp.media import MediaDetectError

    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock()
    monkeypatch.setattr(gemini, "_client", lambda: fake_client)

    async def failing_detect(url: str) -> str:
        raise MediaDetectError(f"HEAD request failed for {url}")

    monkeypatch.setattr("imagine_mcp.media.detect_media_type_async", failing_detect)

    with pytest.raises(MediaDetectError):
        await gemini.understand_multimodal(
            urls=["https://example.com/a.png", "https://example.com/b.png"],
            prompt="describe",
            model="gemini-3.1-pro-preview",
        )
