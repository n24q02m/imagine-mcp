"""Gemini (Google) provider -- fully async via google-genai SDK."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

import platformdirs

from imagine_mcp.errors import ProviderAPIError
from imagine_mcp.providers.base import ClientManager

# Minimal per-tier default (no leaderboard ranking; #461). Used only when the
# caller supplies neither an explicit `model` override nor a matching
# GENERATE_MODELS chain entry.
_GENERATE_DEFAULT_MODEL: dict[tuple[str, str], str] = {
    ("image", "poor"): "gemini-3.1-flash-image-preview",
    ("image", "rich"): "gemini-3-pro-image-preview",
    ("video", "poor"): "veo-3.1-lite-generate-preview",
    ("video", "rich"): "veo-3.1-generate-preview",
}


def _client_factory(api_key: str) -> Any:
    from google import genai

    return genai.Client(api_key=api_key)


_manager = ClientManager(
    provider_name="Gemini",
    env_key="GEMINI_API_KEY",
    settings_attr="gemini_api_key",
    client_factory=_client_factory,
)


def _client() -> Any:
    return _manager.get_client()


def _reset_client() -> None:
    """Test hook: force _client() to re-read settings."""
    _manager.reset()


async def understand_video(
    url: str, prompt: str, model: str, max_tokens: int = 2048
) -> dict[str, Any]:
    """Gemini native video understanding (file upload; not litellm-routed).

    ``model`` is the raw Gemini model id (no ``gemini/`` prefix), resolved by
    the dispatcher from an explicit ``model=`` or the ``UNDERSTAND_MODELS``
    chain -- there is no provider/tier catalog default (#461).
    """
    from google.genai import types

    from imagine_mcp.media import download_to_path_async

    client = _client()

    # Download video securely and upload to Gemini
    tmp_dir = Path(platformdirs.user_cache_dir("imagine-mcp")) / "tmp"
    await asyncio.to_thread(tmp_dir.mkdir, parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"{uuid.uuid4().hex}.mp4"
    await download_to_path_async(url, tmp_path)

    try:
        gfile = await client.aio.files.upload(file=tmp_path)
        resp = await client.aio.models.generate_content(
            model=model,
            contents=[prompt, gfile],
            config=types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
    finally:
        await asyncio.to_thread(tmp_path.unlink, missing_ok=True)

    return {
        "text": resp.text,
        "model": model,
        "provider": "gemini",
    }


async def understand_multimodal(
    urls: list[str],
    prompt: str,
    model: str,
    max_tokens: int = 2048,
    media_types: list[str] | None = None,
) -> dict[str, Any]:
    """Gemini native multimodal: mixed image+video URLs in a single call.

    ``model`` is the raw Gemini model id (no ``gemini/`` prefix); see
    ``understand_video`` for the resolution contract (#461).
    """
    from google.genai import types

    from imagine_mcp.media import (
        detect_media_type_async,
        download_to_path_async,
        get_ssrf_safe_async_client,
        resolve_image_mime,
    )

    client = _client()
    parts: list[Any] = [prompt]
    tmp_files: list[Path] = []

    tmp_dir = Path(platformdirs.user_cache_dir("imagine-mcp")) / "tmp"
    await asyncio.to_thread(tmp_dir.mkdir, parents=True, exist_ok=True)

    try:
        # ⚡ Bolt: Optimize network I/O from O(N) to O(1) latency using asyncio.gather
        # to fetch parts concurrently.
        async def _fetch_part(idx: int, u: str, mt: str) -> Any:
            if mt == "image":
                img_resp = await get_ssrf_safe_async_client().get(
                    u, follow_redirects=True, timeout=60
                )
                img_data = img_resp.content
                mime_type = resolve_image_mime(
                    img_resp.headers.get("content-type"), img_data
                )
                return types.Part.from_bytes(data=img_data, mime_type=mime_type)
            else:
                tmp_path = tmp_dir / f"{uuid.uuid4().hex}.mp4"
                # Register temporary path *before* the await to guarantee it is cleaned up
                # in the finally block if a partial failure occurs.
                tmp_files.append(tmp_path)
                await download_to_path_async(u, tmp_path)
                return await client.aio.files.upload(file=tmp_path)

        async def _resolve_mt(idx: int, u: str) -> str:
            return media_types[idx] if media_types else await detect_media_type_async(u)

        # ⚡ Bolt: Use return_exceptions=True to ensure no background tasks are leaked
        # if one download or upload fails. This also avoids skipping cleanup logic.
        gathered_mts = await asyncio.gather(
            *(_resolve_mt(i, u) for i, u in enumerate(urls)), return_exceptions=True
        )
        resolved_mts: list[str] = []
        for res in gathered_mts:
            if isinstance(res, BaseException):
                raise res
            resolved_mts.append(res)

        results = await asyncio.gather(
            *(_fetch_part(i, urls[i], resolved_mts[i]) for i in range(len(urls))),
            return_exceptions=True,
        )
        for res in results:
            if isinstance(res, BaseException):
                raise res
            parts.append(res)

        resp = await client.aio.models.generate_content(
            model=model,
            contents=parts,
            config=types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
    finally:
        for f in tmp_files:
            await asyncio.to_thread(f.unlink, missing_ok=True)

    return {
        "text": resp.text,
        "model": model,
        "provider": "gemini",
        "multimodal": True,
    }


async def generate_image(
    prompt: str,
    tier: str,
    reference_image_url: str | None = None,
    aspect_ratio: str = "1:1",
    output_mode: str = "both",
    model_id: str | None = None,
) -> dict[str, Any]:
    # native: litellm migration deferred -- probe credential-gated (gemini billing / no openai key 2026-06-11); avideo/aimage param unverified
    from google.genai import types

    from imagine_mcp.media import get_ssrf_safe_async_client, resolve_image_mime

    client = _client()
    # ``model_id`` (from a GENERATE_MODELS chain or explicit override) wins over
    # the provider's minimal per-tier default.
    model = model_id or _GENERATE_DEFAULT_MODEL[("image", tier)]
    contents: list[Any] = [prompt]

    if reference_image_url:
        img_resp = await get_ssrf_safe_async_client().get(
            reference_image_url, follow_redirects=True, timeout=60
        )
        img_data = img_resp.content
        mime_type = resolve_image_mime(img_resp.headers.get("content-type"), img_data)
        contents.append(types.Part.from_bytes(data=img_data, mime_type=mime_type))

    resp = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    image_data: bytes | None = None
    for part in resp.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_data = part.inline_data.data
            break
    if not image_data:
        raise ProviderAPIError("Gemini returned no image", status_code=500)

    from imagine_mcp.media import emit_media

    media_fields = await emit_media(image_data, ".png", "image", output_mode)
    return {
        **media_fields,
        "model": model,
        "provider": "gemini",
        "tier": tier,
    }


async def generate_video(
    prompt: str,
    tier: str,
    reference_image_url: str | None = None,
    job_id: str | None = None,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
    output_mode: str = "both",
    model_id: str | None = None,
) -> dict[str, Any]:
    # native: litellm migration deferred -- probe credential-gated (gemini billing / no openai key 2026-06-11); avideo/aimage param unverified
    from google.genai import types

    # ``model_id`` (from a GENERATE_MODELS chain or explicit override) wins over
    # the provider's minimal per-tier default.
    model = model_id or _GENERATE_DEFAULT_MODEL[("video", tier)]
    client = _client()

    if job_id is None:
        op = await client.aio.models.generate_videos(
            model=model,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                duration_seconds=duration_seconds,
                person_generation="allow_all",
            ),
        )
        return {
            "job_id": op.name,
            "status": "pending",
            "eta_seconds": 60,
            "model": model,
            "provider": "gemini",
            "tier": tier,
        }

    op = await client.aio.operations.get(job_id)
    if not op.done:
        return {"job_id": job_id, "status": "pending", "eta_seconds": 30}

    if op.error:
        raise ProviderAPIError(f"Gemini job error: {op.error}", status_code=500)

    video = op.response.generated_videos[0]
    from imagine_mcp.media import emit_media

    # The async files.download returns the downloaded bytes (unlike the sync
    # client, it does NOT set video.video.video_bytes as a side effect), so
    # capture the return value -- this keeps the video in memory and lets
    # emit_media honour output_mode without persisting on the ephemeral CF FS.
    video_bytes: bytes = await client.aio.files.download(file=video.video)
    media_fields = await emit_media(video_bytes, ".mp4", "video", output_mode)

    return {
        **media_fields,
        "job_id": job_id,
        "status": "done",
        "model": model,
        "provider": "gemini",
        "tier": tier,
    }
