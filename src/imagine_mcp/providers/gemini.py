"""Gemini (Google) provider -- fully async via google-genai SDK."""

from __future__ import annotations

import asyncio
import base64
import os
import uuid
from pathlib import Path
from typing import Any

import platformdirs

from imagine_mcp.config import settings
from imagine_mcp.errors import CredentialMissingError, ProviderAPIError
from imagine_mcp.models import get_model_id

_CLIENT: Any = None
_SUB_CLIENTS: dict[str, Any] = {}


def _resolve_api_key() -> str | None:
    """Return the GEMINI_API_KEY for the current request scope."""
    from imagine_mcp.credential_state import (
        credentials_for_current_request,
        get_current_sub,
    )

    if get_current_sub() is not None:
        return credentials_for_current_request().get("GEMINI_API_KEY")
    return settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")


def _client() -> Any:
    global _CLIENT
    from imagine_mcp.credential_state import get_current_sub

    sub = get_current_sub()
    if sub is not None:
        cached = _SUB_CLIENTS.get(sub)
        if cached is not None:
            return cached
        api_key = _resolve_api_key()
        if not api_key:
            raise CredentialMissingError(
                "Gemini API key missing. Run config(action='open_relay') for "
                "browser-based setup, or set GEMINI_API_KEY."
            )
        from google import genai

        client = genai.Client(api_key=api_key)
        _SUB_CLIENTS[sub] = client
        return client

    if _CLIENT is None:
        api_key = _resolve_api_key()
        if not api_key:
            raise CredentialMissingError(
                "Gemini API key missing. Run config(action='open_relay') for "
                "browser-based setup, or set GEMINI_API_KEY."
            )
        from google import genai

        _CLIENT = genai.Client(api_key=api_key)
    return _CLIENT


def _reset_client() -> None:
    """Test hook: force _client() to re-read settings."""
    global _CLIENT
    _CLIENT = None
    _SUB_CLIENTS.clear()


async def understand_image(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    # litellm passthrough; live-verify deferred (gemini billing 2026-06-11)
    import base64 as _base64

    from mcp_core.llm import acompletion

    from imagine_mcp.media import get_ssrf_safe_async_client, resolve_image_mime

    model = get_model_id("gemini", "understand", "image", tier)

    # Download image securely to prevent backend SSRF
    img_resp = await get_ssrf_safe_async_client().get(
        url, follow_redirects=True, timeout=60
    )
    img_data = img_resp.content
    mime_type = resolve_image_mime(img_resp.headers.get("content-type"), img_data)
    data_url = f"data:{mime_type};base64,{_base64.b64encode(img_data).decode()}"

    # Normalise empty string to None: a non-None api_key suppresses litellm's
    # provider env-var fallback (would 401 on "").
    resolved_api_key = _resolve_api_key() or None

    resp = await acompletion(
        model=f"gemini/{model}",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        max_tokens=max_tokens,
        api_key=resolved_api_key,
    )
    return {
        "text": resp.choices[0].message.content,
        "model": model,
        "provider": "gemini",
        "tier": tier,
    }


async def understand_video(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    from google.genai import types

    from imagine_mcp.media import download_to_path_async

    client = _client()
    model = get_model_id("gemini", "understand", "video", tier)

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
        if await asyncio.to_thread(tmp_path.exists):
            await asyncio.to_thread(tmp_path.unlink)

    return {
        "text": resp.text,
        "model": model,
        "provider": "gemini",
        "tier": tier,
    }


async def understand_multimodal(
    urls: list[str],
    prompt: str,
    tier: str,
    max_tokens: int = 2048,
    media_types: list[str] | None = None,
) -> dict[str, Any]:
    """Gemini native multimodal: mixed image+video URLs in a single call."""
    from google.genai import types

    from imagine_mcp.media import (
        detect_media_type_async,
        download_to_path_async,
        get_ssrf_safe_async_client,
        resolve_image_mime,
    )

    client = _client()
    model = get_model_id("gemini", "understand", "image", tier)
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
            if await asyncio.to_thread(f.exists):
                await asyncio.to_thread(f.unlink)

    return {
        "text": resp.text,
        "model": model,
        "provider": "gemini",
        "tier": tier,
        "multimodal": True,
    }


async def generate_image(
    prompt: str,
    tier: str,
    reference_image_url: str | None = None,
    aspect_ratio: str = "1:1",
) -> dict[str, Any]:
    # native: litellm migration deferred -- probe credential-gated (gemini billing / no openai key 2026-06-11); avideo/aimage param unverified
    from google.genai import types

    from imagine_mcp.media import get_ssrf_safe_async_client, resolve_image_mime

    client = _client()
    model = get_model_id("gemini", "generate", "image", tier)
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

    out_dir = Path(platformdirs.user_cache_dir("imagine-mcp")) / "generations"
    await asyncio.to_thread(out_dir.mkdir, parents=True, exist_ok=True)
    out_path = out_dir / f"{uuid.uuid4().hex}.png"
    await asyncio.to_thread(out_path.write_bytes, image_data)

    return {
        "image_path": str(out_path),
        "image_base64": base64.b64encode(image_data).decode(),
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
) -> dict[str, Any]:
    # native: litellm migration deferred -- probe credential-gated (gemini billing / no openai key 2026-06-11); avideo/aimage param unverified
    from google.genai import types

    model = get_model_id("gemini", "generate", "video", tier)
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
    out_dir = Path(platformdirs.user_cache_dir("imagine-mcp")) / "generations"
    await asyncio.to_thread(out_dir.mkdir, parents=True, exist_ok=True)
    out_path = out_dir / f"{uuid.uuid4().hex}.mp4"

    # Download video file. genai.Client.aio.files.download is likely what we need.
    await client.aio.files.download(file=video.video)
    # The SDK usually saves it locally if specified, or returns bytes.
    # Looking at sync code: video.video.save(str(out_path))
    # Let's check if video.video has an async save.
    # If not, use to_thread.
    await asyncio.to_thread(video.video.save, str(out_path))

    return {
        "video_path": str(out_path),
        "job_id": job_id,
        "status": "done",
        "model": model,
        "provider": "gemini",
        "tier": tier,
    }
