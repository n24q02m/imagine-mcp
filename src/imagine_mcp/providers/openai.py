"""OpenAI provider -- image-only (2 LIVE + 2 ERROR)."""

from __future__ import annotations

import asyncio
import base64
import uuid
from pathlib import Path
from typing import Any

import platformdirs

from imagine_mcp.errors import (
    ProviderAPIError,
    ProviderUnsupportedError,
)
from imagine_mcp.models import get_model_id
from imagine_mcp.providers.base import ClientManager


def _client_factory(api_key: str) -> Any:
    from openai import AsyncOpenAI

    return AsyncOpenAI(api_key=api_key)


_manager = ClientManager(
    provider_name="OpenAI",
    env_key="OPENAI_API_KEY",
    settings_attr="openai_api_key",
    client_factory=_client_factory,
)


def _client() -> Any:
    return _manager.get_client()


def _reset_client() -> None:
    _manager.reset()


async def understand_image(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    # litellm passthrough; live-verify deferred (no openai key 2026-06-11)
    from mcp_core.llm import acompletion

    from imagine_mcp.media import get_ssrf_safe_async_client

    model = get_model_id("openai", "understand", "image", tier)

    # Download image securely and pass as base64 data URL to prevent backend SSRF
    resp_img = await get_ssrf_safe_async_client().get(
        url, follow_redirects=True, timeout=60
    )
    img_b64 = base64.b64encode(resp_img.content).decode()
    mime_type = resp_img.headers.get("content-type", "image/png")
    data_url = f"data:{mime_type};base64,{img_b64}"

    # Normalise empty string to None: a non-None api_key suppresses litellm's
    # provider env-var fallback (would 401 on "").
    resolved_api_key = _manager.get_api_key() or None

    resp = await acompletion(
        model=f"openai/{model}",
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
        "provider": "openai",
        "tier": tier,
    }


async def understand_video(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    raise ProviderUnsupportedError(
        "openai.understand.video: GPT-5.4 is image-only. "
        "Extract frames externally or use provider='gemini'."
    )


async def generate_image(
    prompt: str,
    tier: str,
    reference_image_url: str | None = None,
    aspect_ratio: str = "1:1",
) -> dict[str, Any]:
    # native: litellm migration deferred -- probe credential-gated (gemini billing / no openai key 2026-06-11); avideo/aimage param unverified
    model = get_model_id("openai", "generate", "image", tier)
    size_map = {"1:1": "1024x1024", "16:9": "1792x1024", "9:16": "1024x1792"}
    size = size_map.get(aspect_ratio, "1024x1024")

    if reference_image_url:
        from imagine_mcp.media import get_ssrf_safe_async_client

        img_bytes = (
            await get_ssrf_safe_async_client().get(
                reference_image_url, follow_redirects=True, timeout=60
            )
        ).content
        resp = await _client().images.edit(
            model=model, image=img_bytes, prompt=prompt, size=size
        )
    else:
        resp = await _client().images.generate(
            model=model, prompt=prompt, size=size, n=1
        )

    img_b64 = resp.data[0].b64_json
    if not img_b64:
        raise ProviderAPIError("OpenAI returned no image", status_code=500)
    img_bytes = base64.b64decode(img_b64)

    out_dir = Path(platformdirs.user_cache_dir("imagine-mcp")) / "generations"
    await asyncio.to_thread(out_dir.mkdir, parents=True, exist_ok=True)
    out_path = out_dir / f"{uuid.uuid4().hex}.png"
    await asyncio.to_thread(out_path.write_bytes, img_bytes)

    return {
        "image_path": str(out_path),
        "image_base64": img_b64,
        "model": model,
        "provider": "openai",
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
    raise ProviderUnsupportedError(
        "openai.generate.video: Sora 2 API shutdown 2026-09-24. "
        "Use provider='gemini' (Veo) or 'grok' (Grok Imagine)."
    )
