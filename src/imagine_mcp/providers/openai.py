"""OpenAI provider -- 3 LIVE + 1 ERROR."""

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
from imagine_mcp.models import GenerateParams, get_model_id

_CLIENT: Any = None
# Per-sub client cache for HTTP multi-user mode (see providers/gemini.py).
_SUB_CLIENTS: dict[str, Any] = {}


def _resolve_api_key() -> str | None:
    """Return OPENAI_API_KEY for the current request scope."""
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
        from openai import OpenAI

        api_key = _resolve_api_key()
        if not api_key:
            raise CredentialMissingError(
                "OpenAI API key missing. Run config(action='open_relay') for "
                "browser-based setup, or set OPENAI_API_KEY."
            )
        client = OpenAI(api_key=api_key)
        _SUB_CLIENTS[sub] = client
        return client

    if _CLIENT is None:
        from openai import OpenAI

        api_key = _resolve_api_key()
        if not api_key:
            raise CredentialMissingError(
                "OpenAI API key missing. Run config(action='open_relay') for "
                "browser-based setup, or set OPENAI_API_KEY."
            )
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
    resp = _client().chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": url}},
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
        "openai.understand.video: GPT-5.4 vision is image-only. "
        "Workarounds: (1) use provider='gemini' (native multimodal), or "
        "(2) extract frames externally and pass as image URLs."
    )


def generate_image(
    prompt: str,
    tier: str,
    params: GenerateParams | None = None,
) -> dict[str, Any]:
    params = params or GenerateParams()
    reference_image_url = params.reference_image_url
    aspect_ratio = params.aspect_ratio or "1:1"

    model = get_model_id("openai", "generate", "image", tier)

    # 1:1 -> 1024x1024, 16:9 -> 1792x1024, 9:16 -> 1024x1792
    size = "1024x1024"
    if aspect_ratio == "16:9":
        size = "1792x1024"
    elif aspect_ratio == "9:16":
        size = "1024x1792"

    if reference_image_url:
        from imagine_mcp.media import get_ssrf_safe_client

        img_bytes = (
            get_ssrf_safe_client()
            .get(reference_image_url, follow_redirects=True, timeout=60)
            .content
        )
        resp = _client().images.edit(
            model=model, image=img_bytes, prompt=prompt, size=size
        )
    else:
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


def generate_video(
    prompt: str,
    tier: str,
    params: GenerateParams | None = None,
) -> dict[str, Any]:
    raise ProviderUnsupportedError(
        "openai.generate.video: Sora 2 API shutdown 2026-09-24. "
        "Use provider='gemini' (Veo) or 'grok' (Grok Imagine)."
    )
