"""OpenAI provider -- image-only (1 LIVE + 2 ERROR)."""

from __future__ import annotations

import base64
from typing import Any

from imagine_mcp.errors import (
    ProviderAPIError,
    ProviderUnsupportedError,
)
from imagine_mcp.providers.base import ClientManager

# Minimal per-tier default (no leaderboard ranking; #461). Used only when the
# caller supplies neither an explicit `model` override nor a matching
# GENERATE_MODELS chain entry.
_GENERATE_DEFAULT_MODEL: dict[str, str] = {
    "poor": "gpt-image-1-mini",
    "rich": "gpt-image-1.5",
}


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
    output_mode: str = "both",
    model_id: str | None = None,
) -> dict[str, Any]:
    # native: litellm migration deferred -- probe credential-gated (gemini billing / no openai key 2026-06-11); avideo/aimage param unverified
    # ``model_id`` (from a GENERATE_MODELS chain or explicit override) wins over
    # the provider's minimal per-tier default.
    model = model_id or _GENERATE_DEFAULT_MODEL[tier]
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

    from imagine_mcp.media import emit_media

    media_fields = await emit_media(img_bytes, ".png", "image", output_mode)
    return {
        **media_fields,
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
    output_mode: str = "both",
    model_id: str | None = None,
) -> dict[str, Any]:
    raise ProviderUnsupportedError(
        "openai.generate.video: Sora 2 API shutdown 2026-09-24. "
        "Use provider='gemini' (Veo) or 'grok' (Grok Imagine)."
    )
