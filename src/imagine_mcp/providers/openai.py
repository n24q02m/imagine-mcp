"""OpenAI provider -- images only.

Understand (GPT-5.4 vision) + Generate (DALL-E 3 / cross-gen).
Video returns ProviderUnsupportedError (Sora shutdown 2026-09-24).
"""

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
from imagine_mcp.providers.base import ImageParams, VideoParams

_CLIENT: Any = None
# Per-sub client cache for HTTP multi-user mode (see providers/gemini.py).
_SUB_CLIENTS: dict[str, Any] = {}


def _resolve_api_key() -> str | None:
    """Return the OPENAI_API_KEY for the current request scope.

    Resolution logic matches gemini.py (config.enc > settings > os.environ).
    """
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
    model = get_model_id("openai", "understand", "image", tier)

    # Use base64 data URL to prevent SSRF by having the provider fetch directly
    from imagine_mcp.media import get_ssrf_safe_client

    resp_img = get_ssrf_safe_client().get(url, follow_redirects=True, timeout=60)
    img_b64 = base64.b64encode(resp_img.content).decode()
    mime_type = resp_img.headers.get("content-type", "image/png")
    data_url = f"data:{mime_type};base64,{img_b64}"

    resp = _client().chat.completions.create(
        model=model,
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
    )
    return {
        "text": resp.choices[0].message.content,
        "model": model,
        "provider": "openai",
        "tier": tier,
    }


def understand_video(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    raise ProviderUnsupportedError(
        "openai.understand.video: OpenAI GPT-5.4 vision is image-only. "
        "Use provider='gemini' or extract frames externally."
    )


def generate_image(params: ImageParams) -> dict[str, Any]:
    model = get_model_id("openai", "generate", "image", params.tier)

    # gpt-image models use resolution instead of aspect ratio strings
    size_map = {
        "1:1": "1024x1024",
        "16:9": "1792x1024",
        "9:16": "1024x1792",
    }
    size = size_map.get(params.aspect_ratio, "1024x1024")

    if params.reference_image_url:
        from imagine_mcp.media import get_ssrf_safe_client

        img_bytes = (
            get_ssrf_safe_client()
            .get(params.reference_image_url, follow_redirects=True, timeout=60)
            .content
        )
        resp = _client().images.edit(
            model=model, image=img_bytes, prompt=params.prompt, size=size
        )
    else:
        resp = _client().images.generate(
            model=model, prompt=params.prompt, size=size, n=1
        )

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
        "tier": params.tier,
    }


def generate_video(params: VideoParams) -> dict[str, Any]:
    raise ProviderUnsupportedError(
        "openai.generate.video: Sora 2 API shutdown 2026-09-24. "
        "Use provider='gemini' (Veo) or 'grok' (Grok Imagine)."
    )
