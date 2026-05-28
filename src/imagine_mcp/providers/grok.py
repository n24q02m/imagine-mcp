"""Grok (xAI) provider -- 3 LIVE + 1 ERROR.

Uses OpenAI SDK with xAI base_url for chat completions (understand).
Dedicated endpoints for images and videos via httpx.
"""

from __future__ import annotations

import base64
import os
import urllib.parse
from typing import Any

from imagine_mcp.config import settings
from imagine_mcp.errors import (
    CredentialMissingError,
    ProviderAPIError,
    ProviderUnsupportedError,
)
from imagine_mcp.media import get_temp_media_path
from imagine_mcp.models import get_model_id

_CLIENT: Any = None
_BASE_URL = "https://api.x.ai/v1"
# Per-sub client cache for HTTP multi-user mode (see providers/gemini.py).
_SUB_CLIENTS: dict[str, Any] = {}


def _api_key() -> str:
    """Return XAI_API_KEY for the current request scope.

    Multi-user HTTP requests pull from the per-sub config; single-user /
    stdio falls back to settings + os.environ.
    """
    from imagine_mcp.credential_state import (
        credentials_for_current_request,
        get_current_sub,
    )

    if get_current_sub() is not None:
        key = credentials_for_current_request().get("XAI_API_KEY")
    else:
        key = settings.xai_api_key or os.environ.get("XAI_API_KEY")
    if not key:
        raise CredentialMissingError(
            "xAI (Grok) API key missing. Run config(action='open_relay') for "
            "browser-based setup, or set XAI_API_KEY."
        )
    return key


def _openai_compat_client() -> Any:
    global _CLIENT
    from imagine_mcp.credential_state import get_current_sub

    sub = get_current_sub()
    if sub is not None:
        cached = _SUB_CLIENTS.get(sub)
        if cached is not None:
            return cached
        from openai import OpenAI

        client = OpenAI(api_key=_api_key(), base_url=_BASE_URL)
        _SUB_CLIENTS[sub] = client
        return client

    if _CLIENT is None:
        from openai import OpenAI

        _CLIENT = OpenAI(api_key=_api_key(), base_url=_BASE_URL)
    return _CLIENT


def _reset_client() -> None:
    global _CLIENT
    _CLIENT = None
    _SUB_CLIENTS.clear()


def understand_image(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    from imagine_mcp.media import get_ssrf_safe_client

    model = get_model_id("grok", "understand", "image", tier)

    # Download image securely and pass as base64 data URL to prevent backend SSRF
    resp_img = get_ssrf_safe_client().get(url, follow_redirects=True, timeout=60)
    img_b64 = base64.b64encode(resp_img.content).decode()
    mime_type = resp_img.headers.get("content-type", "image/png")
    data_url = f"data:{mime_type};base64,{img_b64}"

    resp = _openai_compat_client().chat.completions.create(
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
        "provider": "grok",
        "tier": tier,
    }


def understand_video(
    url: str, prompt: str, tier: str, max_tokens: int = 2048
) -> dict[str, Any]:
    raise ProviderUnsupportedError(
        "grok.understand.video: Grok production (4.20-0309-v2) is image-only. "
        "Beta supports video but is not stable. Use provider='gemini'."
    )


def generate_image(
    prompt: str,
    tier: str,
    reference_image_url: str | None = None,
    aspect_ratio: str = "1:1",
) -> dict[str, Any]:
    from imagine_mcp.media import get_ssrf_safe_client

    model = get_model_id("grok", "generate", "image", tier)
    headers = {"Authorization": f"Bearer {_api_key()}"}
    payload: dict[str, Any] = {"model": model, "prompt": prompt, "n": 1}

    if reference_image_url:
        # Download reference image and pass as base64 data URL
        resp_img = get_ssrf_safe_client().get(
            reference_image_url, follow_redirects=True, timeout=60
        )
        img_b64 = base64.b64encode(resp_img.content).decode()
        mime_type = resp_img.headers.get("content-type", "image/png")
        data_url = f"data:{mime_type};base64,{img_b64}"
        payload["reference_image"] = data_url

    from imagine_mcp.media import get_ssrf_safe_client

    resp = get_ssrf_safe_client().post(
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
            get_ssrf_safe_client()
            .get(img_url, follow_redirects=True, timeout=60)
            .content
        ).decode()

    img_bytes = base64.b64decode(img_b64)
    out_path = get_temp_media_path(".png")
    out_path.write_bytes(img_bytes)

    return {
        "image_path": str(out_path),
        "image_base64": img_b64,
        "model": model,
        "provider": "grok",
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
    from imagine_mcp.media import get_ssrf_safe_client

    model = get_model_id("grok", "generate", "video", tier)
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
            resp_img = get_ssrf_safe_client().get(
                reference_image_url, follow_redirects=True, timeout=60
            )
            img_b64 = base64.b64encode(resp_img.content).decode()
            mime_type = resp_img.headers.get("content-type", "image/png")
            data_url = f"data:{mime_type};base64,{img_b64}"
            payload["source_image"] = data_url

        from imagine_mcp.media import get_ssrf_safe_client

        resp = get_ssrf_safe_client().post(
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

    from imagine_mcp.media import get_ssrf_safe_client

    safe_job_id = urllib.parse.quote(job_id, safe="")
    resp = get_ssrf_safe_client().get(
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
        get_ssrf_safe_client()
        .get(video_url, follow_redirects=True, timeout=120)
        .content
    )

    out_path = get_temp_media_path(".mp4")
    out_path.write_bytes(video_bytes)

    return {
        "video_path": str(out_path),
        "video_url": video_url,
        "job_id": job_id,
        "status": "done",
        "model": model,
        "provider": "grok",
        "tier": tier,
    }
