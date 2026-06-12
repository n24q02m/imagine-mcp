"""Validate action/provider/tier/media_type and route to provider module."""

from __future__ import annotations

import asyncio
import base64
import importlib
import os
from typing import Any

from imagine_mcp.errors import (
    CredentialMissingError,
    InvalidMediaTypeError,
    InvalidProviderError,
    InvalidTierError,
    ProviderUnsupportedError,
)
from imagine_mcp.media import detect_media_type_async, validate_url_and_get_ip
from imagine_mcp.models import UNSUPPORTED, get_model_id

VALID_PROVIDERS = ["gemini", "openai", "grok"]
VALID_TIERS = ["poor", "rich"]
VALID_MEDIA_TYPES = ["image", "video"]

# Modes accepted by litellm's registry per action; passed to check_capability.
# A registry-missing model raises nothing (open passthrough), so these only
# guard KNOWN models against an obvious action/mode mismatch.
_UNDERSTAND_MODES: tuple[str, ...] = ("chat", "responses", "completion")

# litellm provider prefix -> env var holding that provider's API key, used to
# resolve a per-sub credential for an explicit passthrough ``model``.
_PREFIX_TO_ENV: dict[str, str] = {
    "gemini": "GEMINI_API_KEY",
    "google": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gpt": "OPENAI_API_KEY",
    "xai": "XAI_API_KEY",
    "grok": "XAI_API_KEY",
}


def _passthrough_api_key(model: str) -> str | None:
    """Resolve the API key for an explicit passthrough ``model``.

    Maps the ``provider/`` prefix to its env var and reads the per-request
    credential view. Returns ``None`` when no prefix or no key is configured;
    a ``None`` key lets litellm fall back to its own env-var lookup.
    """
    from imagine_mcp.credential_state import credentials_for_current_request

    prefix = model.split("/", 1)[0].lower() if "/" in model else ""
    env_var = _PREFIX_TO_ENV.get(prefix)
    if env_var is None:
        return None
    return credentials_for_current_request().get(env_var) or None


# Auto-fallback priority when caller does not pin a provider. Order is
# (XAI, OpenAI, Gemini): Gemini stays last because Google AI Studio
# accounts can be billing-locked at the org level (403 PERMISSION_DENIED
# on every :generateContent call) without warning, so we prefer keys
# that are less prone to silent revocation.
_DEFAULT_PROVIDER_PRIORITY: tuple[tuple[str, str], ...] = (
    ("XAI_API_KEY", "grok"),
    ("OPENAI_API_KEY", "openai"),
    ("GEMINI_API_KEY", "gemini"),
)

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


async def _validate_url(url: str, param: str) -> None:
    """Reject non-http(s) URLs and internal IPs to prevent SSRF."""
    # validate_url_and_get_ip uses a thread pool for DNS internally.
    await asyncio.to_thread(validate_url_and_get_ip, url, param)


def _validate(provider: str, tier: str) -> None:
    if provider not in VALID_PROVIDERS:
        raise InvalidProviderError(
            f"Unknown provider {provider!r}. Valid: {VALID_PROVIDERS}"
        )
    if tier not in VALID_TIERS:
        raise InvalidTierError(f"Unknown tier {tier!r}. Valid: {VALID_TIERS}")


def _default_provider() -> str:
    """Return the first provider whose API key is present for this request."""
    from imagine_mcp.credential_state import credentials_for_current_request

    creds = credentials_for_current_request()
    for env_var, provider in _DEFAULT_PROVIDER_PRIORITY:
        if creds.get(env_var):
            return provider
    keys = ", ".join(env for env, _ in _DEFAULT_PROVIDER_PRIORITY)
    raise CredentialMissingError(
        "No provider API key configured. Set one of: "
        f"{keys}, or run config(action='open_relay') to configure via browser."
    )


def resolve_understand_chain() -> list[str]:
    """Ordered ``UNDERSTAND_MODELS`` chain (litellm ``provider/model`` entries).

    Empty / unset -> empty list, which preserves the provider/tier catalog
    default. The first entry is the primary model; the rest are litellm
    fallbacks.
    """
    raw = (os.getenv("UNDERSTAND_MODELS") or "").strip()
    return [m.strip() for m in raw.split(",") if m.strip()] if raw else []


def _load_provider(provider: str) -> Any:
    return importlib.import_module(f"imagine_mcp.providers.{provider}")


def _unsupported(provider: str, media: str, action: str) -> ProviderUnsupportedError:
    hint = _UNSUPPORTED_HINTS.get((provider, media, action), "")
    msg = f"{provider} does not support {action}.{media}."
    if hint:
        msg += " " + hint
    return ProviderUnsupportedError(msg)


async def _passthrough_understand(
    media_urls: list[str],
    prompt: str,
    model: str,
    max_tokens: int,
    fallbacks: list[str] | None = None,
) -> dict[str, Any]:
    """Understand via an explicit litellm passthrough ``model``.

    Bypasses the provider/tier catalog. Images are downloaded through the
    SSRF-safe client and sent as base64 data URLs (vision message format).
    Registry-missing models pass through with a ``warning`` in the response.

    ``fallbacks`` (the rest of an ``UNDERSTAND_MODELS`` chain after the
    primary) is forwarded to litellm's native ``fallbacks`` kwarg via
    ``acompletion``'s ``**kwargs`` passthrough.
    """
    from mcp_core.llm import (
        ModelCapabilityError,
        acompletion,
        check_capability,
        supports_vision,
    )

    from imagine_mcp.media import get_ssrf_safe_async_client

    if not media_urls:
        raise InvalidMediaTypeError("media_urls is empty")
    for i, u in enumerate(media_urls):
        await _validate_url(u, f"media_urls[{i}]")

    try:
        check_capability(model, _UNDERSTAND_MODES)
    except ModelCapabilityError as e:
        raise ProviderUnsupportedError(str(e)) from e

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]

    async def _fetch_and_encode(u: str) -> dict[str, Any]:
        resp_img = await get_ssrf_safe_async_client().get(
            u, follow_redirects=True, timeout=60
        )
        img_b64 = base64.b64encode(resp_img.content).decode()
        mime_type = resp_img.headers.get("content-type", "image/png")
        data_url = f"data:{mime_type};base64,{img_b64}"
        return {"type": "image_url", "image_url": {"url": data_url}}

    # Optimize sequential asynchronous I/O into concurrent execution
    results = await asyncio.gather(
        *[_fetch_and_encode(u) for u in media_urls], return_exceptions=True
    )
    for res in results:
        if isinstance(res, Exception):
            raise res
        content.append(res)

    resp = await acompletion(
        model=model,
        messages=[{"role": "user", "content": content}],
        max_tokens=max_tokens,
        api_key=_passthrough_api_key(model),
        fallbacks=fallbacks or None,
    )
    out: dict[str, Any] = {
        "text": resp.choices[0].message.content,
        "model": model,
        "provider": "passthrough",
    }
    # supports_vision (public API) returns None for a registry-missing model,
    # which is the same "unknown model -> open passthrough" signal as a missing
    # registry entry -- avoids depending on the private _registry_entry helper.
    if supports_vision(model) is None:
        out["warning"] = (
            f"model {model!r} is not in the litellm registry; "
            "called via open passthrough (capability unverified)."
        )
    return out


async def dispatch_understand(
    media_urls: list[str],
    prompt: str,
    provider: str | None,
    tier: str,
    max_tokens: int = 2048,
    model: str | None = None,
) -> dict[str, Any]:
    """Dispatch understand call to provider (fully async).

    When ``model`` is set, the provider/tier catalog is bypassed and the call
    is routed straight to litellm via ``mcp_core.llm`` (open passthrough).
    """
    if model is not None:
        return await _passthrough_understand(media_urls, prompt, model, max_tokens)

    if model is None and provider is None:
        chain = resolve_understand_chain()
        if chain:
            return await _passthrough_understand(
                media_urls, prompt, chain[0], max_tokens, fallbacks=chain[1:]
            )

    if provider is None:
        provider = _default_provider()
    _validate(provider, tier)
    if not media_urls:
        raise InvalidMediaTypeError("media_urls is empty")

    # Sequential validation to preserve fail-fast and avoid pool deadlocks.
    for i, u in enumerate(media_urls):
        await _validate_url(u, f"media_urls[{i}]")

    # Concurrent media type detection.
    media_types = await asyncio.gather(
        *(detect_media_type_async(u) for u in media_urls)
    )
    has_video = "video" in media_types

    if has_video:
        video_model = get_model_id(provider, "understand", "video", tier)
        if video_model is UNSUPPORTED:
            raise _unsupported(provider, "video", "understand")

    mod = _load_provider(provider)

    # Gemini native multimodal can accept many URLs in one call
    if provider == "gemini" and len(media_urls) > 1:
        return await mod.understand_multimodal(
            media_urls, prompt, tier, max_tokens, media_types=media_types
        )

    url = media_urls[0]
    primary = media_types[0]
    if primary == "image":
        return await mod.understand_image(url, prompt, tier, max_tokens)
    return await mod.understand_video(url, prompt, tier, max_tokens)


# litellm provider prefix -> native generation provider. Generation stays
# 100% native (litellm gen passthrough deferred -- avideo/aimage param
# unverified, probe credential-gated 2026-06-11), so an explicit ``model``
# override on generate is resolved to a native provider rather than routed
# through litellm.
_GEN_PREFIX_TO_PROVIDER: dict[str, str] = {
    "gemini": "gemini",
    "google": "gemini",
    "openai": "openai",
    "gpt": "openai",
    "xai": "grok",
    "grok": "grok",
}


def _resolve_generate_provider(model: str) -> str:
    """Map a passthrough ``model`` prefix to a native generation provider.

    Raises ``ProviderUnsupportedError`` with an explicit litellm-gap message
    when the prefix maps to a provider that has no native generation path
    here (xAI generation runs on raw x.ai endpoints, not litellm).
    """
    prefix = model.split("/", 1)[0].lower() if "/" in model else ""
    mapped = _GEN_PREFIX_TO_PROVIDER.get(prefix)
    if mapped is None:
        raise ProviderUnsupportedError(
            f"litellm gap: generation passthrough for model {model!r} is not "
            "supported. Use an explicit provider/tier instead."
        )
    return mapped


async def dispatch_generate(
    media_type: str,
    prompt: str,
    provider: str | None,
    tier: str,
    reference_image_url: str | None = None,
    job_id: str | None = None,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
    model: str | None = None,
) -> dict[str, Any]:
    """Dispatch generate call to provider (fully async).

    When ``model`` is set, the litellm 'provider/model' prefix selects a
    native generation provider (catalog still picks the concrete model by
    tier); generation itself is never routed through litellm.
    """
    if model is not None:
        provider = _resolve_generate_provider(model)
    elif provider is None:
        provider = _default_provider()
    _validate(provider, tier)
    if media_type not in VALID_MEDIA_TYPES:
        raise InvalidMediaTypeError(
            f"Unknown media_type {media_type!r}. Valid: {VALID_MEDIA_TYPES}"
        )
    if reference_image_url is not None:
        await _validate_url(reference_image_url, "reference_image_url")

    catalog_model = get_model_id(provider, "generate", media_type, tier)
    if catalog_model is UNSUPPORTED:
        raise _unsupported(provider, media_type, "generate")

    mod = _load_provider(provider)
    if media_type == "image":
        return await mod.generate_image(prompt, tier, reference_image_url, aspect_ratio)
    return await mod.generate_video(
        prompt, tier, reference_image_url, job_id, aspect_ratio, duration_seconds
    )
