"""Gemini provider -- all 4 actions LIVE using google-genai SDK."""

from __future__ import annotations

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


def _client() -> Any:
    global _CLIENT
    if _CLIENT is None:
        api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
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


def understand_image(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    from google.genai import types

    model = get_model_id("gemini", "understand", "image", tier)
    resp = _client().models.generate_content(
        model=model,
        contents=[prompt, types.Part.from_uri(file_uri=url, mime_type="image/png")],
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

    model = get_model_id("gemini", "understand", "video", tier)
    resp = _client().models.generate_content(
        model=model,
        contents=[prompt, types.Part.from_uri(file_uri=url, mime_type="video/mp4")],
        config=types.GenerateContentConfig(max_output_tokens=max_tokens),
    )
    return {
        "text": resp.text,
        "model": model,
        "provider": "gemini",
        "tier": tier,
    }


def understand_multimodal(
    urls: list[str], prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    """Gemini native multimodal: mixed image+video URLs in a single call."""
    from google.genai import types

    from imagine_mcp.media import detect_media_type

    model = get_model_id("gemini", "understand", "image", tier)
    parts: list[Any] = [prompt]
    for u in urls:
        mt = detect_media_type(u)
        mime = "image/png" if mt == "image" else "video/mp4"
        parts.append(types.Part.from_uri(file_uri=u, mime_type=mime))
    resp = _client().models.generate_content(
        model=model,
        contents=parts,
        config=types.GenerateContentConfig(max_output_tokens=max_tokens),
    )
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

    model = get_model_id("gemini", "generate", "image", tier)
    contents: list[Any] = [prompt]
    if reference_image_url:
        contents.append(
            types.Part.from_uri(file_uri=reference_image_url, mime_type="image/png")
        )

    resp = _client().models.generate_content(
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
