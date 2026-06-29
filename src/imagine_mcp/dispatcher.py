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


# Native generation provider -> its API-key env var. Built from the auto-
# fallback priority so the two stay in lock-step.
_PROVIDER_TO_ENV: dict[str, str] = {
    provider: env_var for env_var, provider in _DEFAULT_PROVIDER_PRIORITY
}


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


def _default_generate_provider() -> str:
    """Auto-fallback provider for generation, honouring the sub-aware order.

    Walks ``resolve_generate_provider_priority()`` (default = the native
    ``_DEFAULT_PROVIDER_PRIORITY`` order) and returns the first provider whose
    API key is present for this request. Raises ``CredentialMissingError`` when
    none of the ordered providers has a key.
    """
    from imagine_mcp.credential_state import credentials_for_current_request

    creds = credentials_for_current_request()
    order = resolve_generate_provider_priority()
    for provider in order:
        env_var = _PROVIDER_TO_ENV.get(provider)
        if env_var and creds.get(env_var):
            return provider
    keys = ", ".join(_PROVIDER_TO_ENV.values())
    raise CredentialMissingError(
        "No provider API key configured. Set one of: "
        f"{keys}, or run config(action='open_relay') to configure via browser."
    )


def _csv_chain(raw: str | None) -> list[str]:
    """Split a CSV config value into a clean ordered list (blanks dropped)."""
    raw = (raw or "").strip()
    return [m.strip() for m in raw.split(",") if m.strip()] if raw else []


def resolve_understand_chain() -> list[str]:
    """Ordered ``UNDERSTAND_MODELS`` chain (litellm ``provider/model`` entries).

    Sub-aware: in multi-user HTTP mode the relay-submitted chain is stored
    per-sub (``credential_state.store_for_sub``) and read back via the per-sub
    accessor -- never from ``os.environ`` (that would leak one sub's chain to a
    concurrent request of another). Single-user / stdio reads ``os.getenv``.

    Empty / unset -> empty list, which preserves the provider/tier catalog
    default. The first entry is the primary model; the rest are litellm
    fallbacks.
    """
    from imagine_mcp.credential_state import config_value_for_current_request

    return _csv_chain(config_value_for_current_request("UNDERSTAND_MODELS"))


def resolve_generate_chain() -> list[str]:
    """Ordered ``GENERATE_MODELS`` chain (litellm ``provider/model`` entries).

    Sub-aware (same isolation contract as ``resolve_understand_chain``). When
    set, the first entry's ``provider/`` prefix selects the native generation
    provider and its model segment OVERRIDES the catalog ``model_id``. Empty /
    unset -> empty list (catalog default preserved).
    """
    from imagine_mcp.credential_state import config_value_for_current_request

    return _csv_chain(config_value_for_current_request("GENERATE_MODELS"))


def resolve_generate_provider_priority() -> list[str]:
    """Ordered generation provider auto-fallback for the active request.

    Sub-aware ``GENERATE_PROVIDER_PRIORITY`` (CSV of provider names). When
    unset, defaults to the native ``_DEFAULT_PROVIDER_PRIORITY`` order. Only
    used when no explicit provider and no ``GENERATE_MODELS`` chain is given.
    """
    from imagine_mcp.credential_state import config_value_for_current_request

    custom = _csv_chain(config_value_for_current_request("GENERATE_PROVIDER_PRIORITY"))
    if custom:
        return custom
    return [provider for _env, provider in _DEFAULT_PROVIDER_PRIORITY]


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

    try:
        check_capability(model, _UNDERSTAND_MODES)
    except ModelCapabilityError as e:
        raise ProviderUnsupportedError(str(e)) from e

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]

    # ⚡ Bolt: Pipeline URL validation and image fetching per URL to eliminate barrier synchronization delays.
    async def _validate_and_fetch_image(i: int, u: str) -> dict[str, Any]:
        await _validate_url(u, f"media_urls[{i}]")
        resp_img = await get_ssrf_safe_async_client().get(
            u, follow_redirects=True, timeout=60
        )
        img_b64 = base64.b64encode(resp_img.content).decode()
        mime_type = resp_img.headers.get("content-type", "image/png")
        data_url = f"data:{mime_type};base64,{img_b64}"
        return {"type": "image_url", "image_url": {"url": data_url}}

    # ⚡ Bolt: Use return_exceptions=True to ensure no background tasks are leaked
    # if one fetch fails. We then explicitly check and raise the first exception.
    results = await asyncio.gather(
        *(_validate_and_fetch_image(i, u) for i, u in enumerate(media_urls)),
        return_exceptions=True,
    )
    for res in results:
        if isinstance(res, BaseException):
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

    # ⚡ Bolt: Pipeline URL validation and media type detection per URL to eliminate barrier synchronization delays.
    async def _process_url(i: int, u: str) -> str:
        await _validate_url(u, f"media_urls[{i}]")
        return await detect_media_type_async(u)

    # return_exceptions=True prevents background tasks from leaking on failure.
    results = await asyncio.gather(
        *(_process_url(i, u) for i, u in enumerate(media_urls)),
        return_exceptions=True,
    )
    media_types: list[str] = []
    for res in results:
        if isinstance(res, BaseException):
            raise res
        media_types.append(res)
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
    output_mode: str = "both",
) -> dict[str, Any]:
    """Dispatch generate call to provider (fully async).

    Provider + model resolution precedence (highest first):

    1. Explicit ``model`` ('provider/model'): prefix selects the native
       generation provider and its model segment overrides the catalog
       ``model_id``; generation itself is never routed through litellm.
    2. Explicit ``provider``: catalog path (catalog picks the model by tier).
    3. ``GENERATE_MODELS`` chain (sub-aware): the first entry's prefix selects
       the provider and its model segment overrides the catalog ``model_id``.
    4. Auto-fallback: ``resolve_generate_provider_priority()`` (sub-aware,
       defaults to the native priority) picks the first provider with a key;
       the catalog supplies the model.

    ``output_mode`` controls how generated media is returned:
    ``"base64"`` (no disk write -- required on ephemeral CF FS),
    ``"path"`` (on-disk path only), or ``"both"`` (default). The deploy-level
    env var ``IMAGINE_OUTPUT_MODE`` overrides the caller's value when set, so a
    serverless operator can force base64 across every request.
    """
    effective_output_mode = os.getenv("IMAGINE_OUTPUT_MODE") or output_mode

    model_id_override: str | None = None
    if model is not None:
        provider = _resolve_generate_provider(model)
        model_id_override = model.split("/", 1)[1] if "/" in model else model
    elif provider is None:
        chain = resolve_generate_chain()
        if chain:
            entry = chain[0]
            provider = _resolve_generate_provider(entry)
            model_id_override = entry.split("/", 1)[1] if "/" in entry else entry
        else:
            provider = _default_generate_provider()
    _validate(provider, tier)
    if media_type not in VALID_MEDIA_TYPES:
        raise InvalidMediaTypeError(
            f"Unknown media_type {media_type!r}. Valid: {VALID_MEDIA_TYPES}"
        )
    if reference_image_url is not None:
        await _validate_url(reference_image_url, "reference_image_url")

    # When an explicit model override is supplied, the catalog lookup is only a
    # support guard (an UNSUPPORTED combo still cannot be served natively).
    catalog_model = get_model_id(provider, "generate", media_type, tier)
    if catalog_model is UNSUPPORTED:
        raise _unsupported(provider, media_type, "generate")

    mod = _load_provider(provider)
    if media_type == "image":
        return await mod.generate_image(
            prompt,
            tier,
            reference_image_url,
            aspect_ratio,
            effective_output_mode,
            model_id=model_id_override,
        )
    return await mod.generate_video(
        prompt,
        tier,
        reference_image_url,
        job_id,
        aspect_ratio,
        duration_seconds,
        effective_output_mode,
        model_id=model_id_override,
    )
