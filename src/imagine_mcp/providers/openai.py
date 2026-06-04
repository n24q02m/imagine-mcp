"""OpenAI provider -- image-only (2 LIVE + 2 ERROR)."""

from __future__ import annotations

import base64
import os
import uuid
from pathlib import Path
from typing import Any

import platformdirs

from imagine_mcp.config import settings
from imagine_mcp.errors import (
    CredentialMissingError,
    ProviderAPIError,
    ProviderUnsupportedError,
)
from imagine_mcp.models import get_model_id

_CLIENT: Any = None
# Per-sub client cache for HTTP multi-user mode. See providers/gemini.py
# for rationale; module-level ``_CLIENT`` still serves stdio + single-user.
_SUB_CLIENTS: dict[str, Any] = {}


def _resolve_api_key() -> str | None:
    """Return OPENAI_API_KEY for the current request scope (per-sub or env)."""
    from imagine_mcp.credential_state import (
        credentials_for_current_request,
        get_current_sub,
    )

    if get_current_sub() is not None:
        return credentials_for_current_request().get("OPENAI_API_KEY")
    return settings.openai_api_key or os.environ.get("OPENAI_API_KEY")


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
                "OpenAI API key missing. Run config(action='open_relay') for "
                "browser-based setup, or set OPENAI_API_KEY."
            )
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        _SUB_CLIENTS[sub] = client
        return client

    if _CLIENT is None:
        api_key = _resolve_api_key()
        if not api_key:
            raise CredentialMissingError(
                "OpenAI API key missing. Run config(action='open_relay') for "
                "browser-based setup, or set OPENAI_API_KEY."
            )
        from openai import OpenAI

        _CLIENT = OpenAI(api_key=api_key)
    return _CLIENT


def _reset_client() -> None:
    global _CLIENT
    _CLIENT = None
    _SUB_CLIENTS.clear()


def understand_image(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    from imagine_mcp.media import get_ssrf_safe_client

    model = get_model_id("openai", "understand", "image", tier)

    # Download image securely and pass as base64 data URL to prevent backend SSRF
    resp_img = get_ssrf_safe_client().get(url, follow_redirects=True, timeout=60)
    img_b64 = base64.b64encode(resp_img.content).decode()
    mime_type = resp_img.headers.get("content-type", "image/png")
    data_url = f"data:{mime_type};base64,{img_b64}"

    resp = _client().responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
        max_output_tokens=max_tokens,
    )
    return {
        "text": resp.output_text,
        "model": model,
        "provider": "openai",
        "tier": tier,
    }


def understand_video(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    raise ProviderUnsupportedError(
        "openai.understand.video: GPT-5.4 vision is image-only. Workarounds: "
        "(1) use provider='gemini' (native multimodal), or "
        "(2) extract frames externally and pass as image URLs."
    )


def edit(
    url: str,
    prompt: str,
    tier: str,
    aspect_ratio: str = "1:1",
) -> dict[str, Any]:
    """Edit an image using OpenAI DALL-E 2."""
    from imagine_mcp.media import get_ssrf_safe_client

    model = get_model_id("openai", "generate", "image", tier)
    size_map = {"1:1": "1024x1024", "16:9": "1792x1024", "9:16": "1024x1792"}
    size = size_map.get(aspect_ratio, "1024x1024")

    # Download reference image securely to prevent backend SSRF
    img_bytes = (
        get_ssrf_safe_client().get(url, follow_redirects=True, timeout=60).content
    )

    resp = _client().images.edit(model=model, image=img_bytes, prompt=prompt, size=size)

    img_b64 = resp.data[0].b64_json
    if not img_b64:
        raise ProviderAPIError("OpenAI returned no image", status_code=500)
    img_bytes = base64.b64decode(img_b64)

    out_dir = Path(platformdirs.user_cache_dir("imagine-mcp")) / "generations"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{uuid.uuid4().hex}.png"
    out_path.write_bytes(img_bytes)

    return {
        "image_path": str(out_path),
        "image_base64": img_b64,
        "model": model,
        "provider": "openai",
        "tier": tier,
    }


def generate_image(
    prompt: str,
    tier: str,
    reference_image_url: str | None = None,
    aspect_ratio: str = "1:1",
) -> dict[str, Any]:
    if reference_image_url:
        return edit(reference_image_url, prompt, tier, aspect_ratio)

    model = get_model_id("openai", "generate", "image", tier)
    size_map = {"1:1": "1024x1024", "16:9": "1792x1024", "9:16": "1024x1792"}
    size = size_map.get(aspect_ratio, "1024x1024")

    resp = _client().images.generate(model=model, prompt=prompt, size=size, n=1)

    img_b64 = resp.data[0].b64_json
    if not img_b64:
        raise ProviderAPIError("OpenAI returned no image", status_code=500)
    img_bytes = base64.b64decode(img_b64)

    out_dir = Path(platformdirs.user_cache_dir("imagine-mcp")) / "generations"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{uuid.uuid4().hex}.png"
    out_path.write_bytes(img_bytes)

    return {
        "image_path": str(out_path),
        "image_base64": img_b64,
        "model": model,
        "provider": "openai",
        "tier": tier,
    }


def video_status(
    job_id: str,
    prompt: str,
    tier: str,
    reference_image_url: str | None = None,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
) -> dict[str, Any]:
    """Proxy for generate_video status polling."""
    return generate_video(
        prompt, tier, reference_image_url, job_id, aspect_ratio, duration_seconds
    )


def generate_video(
    prompt: str,
    tier: str,
    reference_image_url: str | None = None,
    job_id: str | None = None,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
) -> dict[str, Any]:
    raise ProviderUnsupportedError(
        "openai.generate.video: Sora 2 API shutdown 2026-09-24. "
        "Use provider='gemini' (Veo 3.1) or 'grok' (Grok Imagine)."
    )
