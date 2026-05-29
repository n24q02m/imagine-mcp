"""Gemini provider -- all 4 actions LIVE using google-genai SDK."""

from __future__ import annotations

import base64
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import platformdirs

from imagine_mcp.config import settings
from imagine_mcp.errors import CredentialMissingError, ProviderAPIError
from imagine_mcp.models import get_model_id

_CLIENT: Any = None
# Per-sub client cache for HTTP multi-user mode. Keyed by JWT sub so each
# user gets a client wired to their own ``GEMINI_API_KEY``. Single-user /
# stdio mode still uses the module-level ``_CLIENT`` above.
_SUB_CLIENTS: dict[str, Any] = {}

# Thread pool for parallelizing network-bound I/O during multimodal ingestion
# Bounded to 10 workers to avoid overwhelming rate limits while significantly
# reducing sequential latency for multiple URLs.
_GEMINI_POOL = ThreadPoolExecutor(max_workers=10)


def _resolve_api_key() -> str | None:
    """Return the GEMINI_API_KEY for the current request scope.

    Multi-user HTTP path uses the per-sub config from PerPluginStore. The
    settings singleton is read first (frozen at import) for backwards
    compatibility, then ``credentials_for_current_request()`` which falls
    back to ``os.environ`` when no sub is active.
    """
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


def understand_image(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    from google.genai import types

    from imagine_mcp.media import get_ssrf_safe_client

    client = _client()
    model = get_model_id("gemini", "understand", "image", tier)

    # Download image securely to prevent backend SSRF
    img_data = (
        get_ssrf_safe_client().get(url, follow_redirects=True, timeout=60).content
    )

    resp = client.models.generate_content(
        model=model,
        contents=[
            prompt,
            types.Part.from_bytes(data=img_data, mime_type="image/png"),
        ],
        config=types.GenerateContentConfig(max_output_tokens=max_tokens),
    )
    return {
        "text": resp.text,
        "model": model,
        "provider": "gemini",
        "tier": tier,
    }


def understand_video(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    from google.genai import types

    from imagine_mcp.media import download_to_path

    client = _client()
    model = get_model_id("gemini", "understand", "video", tier)

    # Download video securely and upload to Gemini
    tmp_dir = Path(platformdirs.user_cache_dir("imagine-mcp")) / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"{uuid.uuid4().hex}.mp4"
    download_to_path(url, tmp_path)

    try:
        gfile = client.files.upload(file=tmp_path)
        resp = client.models.generate_content(
            model=model,
            contents=[prompt, gfile],
            config=types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    return {
        "text": resp.text,
        "model": model,
        "provider": "gemini",
        "tier": tier,
    }


def understand_multimodal(
    urls: list[str],
    prompt: str,
    tier: str,
    max_tokens: int = 2048,
    media_types: list[str] | None = None,
) -> dict[str, Any]:
    """Gemini native multimodal: mixed image+video URLs in a single call."""
    from google.genai import types

    from imagine_mcp.media import (
        detect_media_type,
        download_to_path,
        get_ssrf_safe_client,
    )

    client = _client()
    model = get_model_id("gemini", "understand", "image", tier)
    parts: list[Any] = [prompt]
    tmp_files: list[Path] = []

    tmp_dir = Path(platformdirs.user_cache_dir("imagine-mcp")) / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:

        def _process_url(idx_and_url: tuple[int, str]) -> tuple[Any, Path | None]:
            i, u = idx_and_url
            mt = media_types[i] if media_types else detect_media_type(u)
            if mt == "image":
                img_data = (
                    get_ssrf_safe_client()
                    .get(u, follow_redirects=True, timeout=60)
                    .content
                )
                return types.Part.from_bytes(data=img_data, mime_type="image/png"), None
            else:
                tmp_path = tmp_dir / f"{uuid.uuid4().hex}.mp4"
                download_to_path(u, tmp_path)
                return client.files.upload(file=tmp_path), tmp_path

        # Parallelize network-bound URL processing (image fetching, video downloading, and uploading)
        futures = []
        for i, u in enumerate(urls):
            futures.append(_GEMINI_POOL.submit(_process_url, (i, u)))

        for future in futures:
            part, temp_file_path = future.result()
            parts.append(part)
            if temp_file_path:
                tmp_files.append(temp_file_path)

        resp = client.models.generate_content(
            model=model,
            contents=parts,
            config=types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
    finally:
        for f in tmp_files:
            if f.exists():
                f.unlink()

    return {
        "text": resp.text,
        "model": model,
        "provider": "gemini",
        "tier": tier,
        "multimodal": True,
    }


def generate_image(
    prompt: str,
    tier: str,
    reference_image_url: str | None = None,
    aspect_ratio: str = "1:1",
) -> dict[str, Any]:
    from google.genai import types

    from imagine_mcp.media import get_ssrf_safe_client

    client = _client()
    model = get_model_id("gemini", "generate", "image", tier)
    contents: list[Any] = [prompt]

    if reference_image_url:
        img_data = (
            get_ssrf_safe_client()
            .get(reference_image_url, follow_redirects=True, timeout=60)
            .content
        )
        contents.append(types.Part.from_bytes(data=img_data, mime_type="image/png"))

    resp = client.models.generate_content(
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
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{uuid.uuid4().hex}.png"
    out_path.write_bytes(image_data)

    return {
        "image_path": str(out_path),
        "image_base64": base64.b64encode(image_data).decode(),
        "model": model,
        "provider": "gemini",
        "tier": tier,
    }


def generate_video(
    prompt: str,
    tier: str,
    reference_image_url: str | None = None,
    job_id: str | None = None,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
) -> dict[str, Any]:
    from google.genai import types

    model = get_model_id("gemini", "generate", "video", tier)
    client = _client()

    if job_id is None:
        # Original code did not use reference_image_url here.
        # Keeping it consistent for now but ensuring we don't pass it to the backend.
        op = client.models.generate_videos(
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

    op = client.operations.get(job_id)
    if not op.done:
        return {"job_id": job_id, "status": "pending", "eta_seconds": 30}

    if op.error:
        raise ProviderAPIError(f"Gemini job error: {op.error}", status_code=500)

    video = op.response.generated_videos[0]
    out_dir = Path(platformdirs.user_cache_dir("imagine-mcp")) / "generations"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{uuid.uuid4().hex}.mp4"
    client.files.download(file=video.video)
    video.video.save(str(out_path))

    return {
        "video_path": str(out_path),
        "job_id": job_id,
        "status": "done",
        "model": model,
        "provider": "gemini",
        "tier": tier,
    }
