"""Validate action/provider/tier/media_type and route to provider module."""

from __future__ import annotations

import importlib
from typing import Any

from imagine_mcp.errors import (
    InvalidMediaTypeError,
    InvalidProviderError,
    InvalidTierError,
    ProviderUnsupportedError,
)
from imagine_mcp.media import detect_media_type
from imagine_mcp.models import UNSUPPORTED, get_model_id

VALID_PROVIDERS = ["gemini", "openai", "grok"]
VALID_TIERS = ["poor", "rich"]
VALID_MEDIA_TYPES = ["image", "video"]

_UNSUPPORTED_HINTS: dict[tuple[str, str, str], str] = {
    ("openai", "video", "understand"): (
        "OpenAI GPT-5.4 vision is image-only. Workarounds: "
        "(1) use provider='gemini' (native multimodal), or "
        "(2) extract frames externally and pass as image URLs."
    ),
    ("openai", "video", "generate"): (
        "OpenAI Sora 2 API is shutting down 2026-09-24. "
        "Use provider='gemini' (Veo 3.1) or 'grok' (Grok Imagine)."
    ),
    ("grok", "video", "understand"): (
        "Grok production (4.20-0309-v2) is image-only. "
        "Use provider='gemini' for video understanding."
    ),
}


def _validate(provider: str, tier: str) -> None:
    if provider not in VALID_PROVIDERS:
        raise InvalidProviderError(
            f"Unknown provider {provider!r}. Valid: {VALID_PROVIDERS}"
        )
    if tier not in VALID_TIERS:
        raise InvalidTierError(f"Unknown tier {tier!r}. Valid: {VALID_TIERS}")


def _load_provider(provider: str) -> Any:
    return importlib.import_module(f"imagine_mcp.providers.{provider}")


def _unsupported(provider: str, media: str, action: str) -> ProviderUnsupportedError:
    hint = _UNSUPPORTED_HINTS.get((provider, media, action), "")
    msg = f"{provider} does not support {action}.{media}."
    if hint:
        msg += " " + hint
    return ProviderUnsupportedError(msg)


def dispatch_understand(
    media_urls: list[str],
    prompt: str,
    provider: str,
    tier: str,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """Dispatch understand call to provider."""
    _validate(provider, tier)
    if not media_urls:
        raise InvalidMediaTypeError("media_urls is empty")

    media_types = [detect_media_type(u) for u in media_urls]
    has_video = "video" in media_types

    if has_video:
        model = get_model_id(provider, "understand", "video", tier)
        if model is UNSUPPORTED:
            raise _unsupported(provider, "video", "understand")

    mod = _load_provider(provider)

    # Gemini native multimodal can accept many URLs in one call
    if provider == "gemini" and len(media_urls) > 1:
        return mod.understand_multimodal(media_urls, prompt, tier, max_tokens)

    url = media_urls[0]
    primary = media_types[0]
    if primary == "image":
        return mod.understand_image(url, prompt, tier, max_tokens)
    return mod.understand_video(url, prompt, tier, max_tokens)


def dispatch_generate(
    media_type: str,
    prompt: str,
    provider: str,
    tier: str,
    reference_image_url: str | None = None,
    job_id: str | None = None,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
) -> dict[str, Any]:
    """Dispatch generate call to provider."""
    _validate(provider, tier)
    if media_type not in VALID_MEDIA_TYPES:
        raise InvalidMediaTypeError(
            f"Unknown media_type {media_type!r}. Valid: {VALID_MEDIA_TYPES}"
        )

    model = get_model_id(provider, "generate", media_type, tier)
    if model is UNSUPPORTED:
        raise _unsupported(provider, media_type, "generate")

    mod = _load_provider(provider)
    if media_type == "image":
        return mod.generate_image(prompt, tier, reference_image_url, aspect_ratio)
    return mod.generate_video(
        prompt, tier, reference_image_url, job_id, aspect_ratio, duration_seconds
    )
