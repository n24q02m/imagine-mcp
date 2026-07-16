"""Grok (xAI) provider -- 2 LIVE + 1 ERROR.

Image/video generation via dedicated httpx endpoints. Image understanding is
handled by ``dispatcher._passthrough_understand`` (litellm), not natively here.
"""

from __future__ import annotations

import base64
import urllib.parse
from typing import Any

from imagine_mcp.errors import (
    ProviderAPIError,
    ProviderUnsupportedError,
)
from imagine_mcp.media import get_ssrf_safe_async_client
from imagine_mcp.providers.base import ClientManager

_BASE_URL = "https://api.x.ai/v1"

# Minimal per-tier default (no leaderboard ranking; #461). Used only when the
# caller supplies neither an explicit `model` override nor a matching
# GENERATE_MODELS chain entry. Video is single-tier (same model for poor/rich).
_GENERATE_DEFAULT_MODEL: dict[tuple[str, str], str] = {
    ("image", "poor"): "grok-imagine-image",
    ("image", "rich"): "grok-imagine-image-pro",
    ("video", "poor"): "grok-imagine-video",
    ("video", "rich"): "grok-imagine-video",
}

_manager = ClientManager(
    provider_name="xAI (Grok)",
    env_key="XAI_API_KEY",
    settings_attr="xai_api_key",
)


def _api_key() -> str:
    """Return XAI_API_KEY for the current request scope."""
    return _manager.get_api_key()


async def understand_video(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    raise ProviderUnsupportedError(
        "grok.understand.video: Grok production (4.20-0309-v2) is image-only. "
        "Beta supports video but is not stable. Use provider='gemini'."
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
    model = model_id or _GENERATE_DEFAULT_MODEL[("image", tier)]
    headers = {"Authorization": f"Bearer {_api_key()}"}
    payload: dict[str, Any] = {"model": model, "prompt": prompt, "n": 1}

    if reference_image_url:
        # Download reference image and pass as base64 data URL
        resp_img = await get_ssrf_safe_async_client().get(
            reference_image_url, follow_redirects=True, timeout=60
        )
        img_b64 = base64.b64encode(resp_img.content).decode()
        mime_type = resp_img.headers.get("content-type", "image/png")
        data_url = f"data:{mime_type};base64,{img_b64}"
        payload["reference_image"] = data_url

    resp = await get_ssrf_safe_async_client().post(
        f"{_BASE_URL}/images/generations",
        json=payload,
        headers=headers,
        timeout=120,
        follow_redirects=True,
    )
    if resp.status_code != 200:
        raise ProviderAPIError(
            f"Grok image generate failed: {resp.text}",
            status_code=resp.status_code,
        )

    data = resp.json()
    img_b64 = data["data"][0].get("b64_json")
    if not img_b64:
        img_url = data["data"][0].get("url")
        img_b64 = base64.b64encode(
            (
                await get_ssrf_safe_async_client().get(
                    img_url, follow_redirects=True, timeout=60
                )
            ).content
        ).decode()

    img_bytes = base64.b64decode(img_b64)

    from imagine_mcp.media import emit_media

    media_fields = await emit_media(img_bytes, ".png", "image", output_mode)
    return {
        **media_fields,
        "model": model,
        "provider": "grok",
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
    # ``model_id`` (from a GENERATE_MODELS chain or explicit override) wins over
    # the provider's minimal per-tier default.
    model = model_id or _GENERATE_DEFAULT_MODEL[("video", tier)]
    headers = {"Authorization": f"Bearer {_api_key()}"}

    if job_id is None:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "duration_seconds": duration_seconds,
            "aspect_ratio": aspect_ratio,
        }
        if reference_image_url:
            # Download source image and pass as base64 data URL
            resp_img = await get_ssrf_safe_async_client().get(
                reference_image_url, follow_redirects=True, timeout=60
            )
            img_b64 = base64.b64encode(resp_img.content).decode()
            mime_type = resp_img.headers.get("content-type", "image/png")
            data_url = f"data:{mime_type};base64,{img_b64}"
            payload["source_image"] = data_url

        resp = await get_ssrf_safe_async_client().post(
            f"{_BASE_URL}/videos/generations",
            json=payload,
            headers=headers,
            timeout=60,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            raise ProviderAPIError(
                f"Grok video submit failed: {resp.text}",
                status_code=resp.status_code,
            )
        data = resp.json()
        return {
            "job_id": data["id"],
            "status": "pending",
            "eta_seconds": data.get("eta_seconds", 30),
            "model": model,
            "provider": "grok",
            "tier": tier,
        }

    safe_job_id = urllib.parse.quote(job_id, safe="")
    resp = await get_ssrf_safe_async_client().get(
        f"{_BASE_URL}/videos/generations/{safe_job_id}",
        headers=headers,
        timeout=30,
        follow_redirects=True,
    )
    if resp.status_code != 200:
        raise ProviderAPIError(
            f"Grok video poll failed: {resp.text}",
            status_code=resp.status_code,
        )
    data = resp.json()

    if data["status"] == "pending":
        return {
            "job_id": job_id,
            "status": "pending",
            "eta_seconds": data.get("eta_seconds", 15),
        }

    if data["status"] == "failed":
        raise ProviderAPIError(
            f"Grok video generation failed: {data.get('error', 'unknown')}",
            status_code=500,
        )

    video_url = data["video_url"]
    video_bytes = (
        await get_ssrf_safe_async_client().get(
            video_url, follow_redirects=True, timeout=120
        )
    ).content

    from imagine_mcp.media import emit_media

    media_fields = await emit_media(video_bytes, ".mp4", "video", output_mode)
    return {
        **media_fields,
        "video_url": video_url,
        "job_id": job_id,
        "status": "done",
        "model": model,
        "provider": "grok",
        "tier": tier,
    }
