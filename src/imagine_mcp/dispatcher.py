"""Validate action/provider/tier/media_type and route to provider module."""

from __future__ import annotations

import importlib
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from imagine_mcp.errors import (
    CredentialMissingError,
    InvalidMediaTypeError,
    InvalidProviderError,
    InvalidTierError,
    ProviderUnsupportedError,
)
from imagine_mcp.media import detect_media_type, validate_url_and_get_ip
from imagine_mcp.models import UNSUPPORTED, get_model_id

VALID_PROVIDERS = ["gemini", "openai", "grok"]
VALID_TIERS = ["poor", "rich"]
VALID_MEDIA_TYPES = ["image", "video"]

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

_DISPATCH_POOL = ThreadPoolExecutor(max_workers=16, thread_name_prefix="dispatcher")

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


def _validate_url(url: str, param: str) -> None:
    """Reject non-http(s) URLs and internal IPs to prevent SSRF.

    This function calls the centralized validation utility which ensures
    the URL uses an allowed scheme and resolves to a public, non-multicast IP.
    """
    validate_url_and_get_ip(url, param)


def _validate(provider: str, tier: str) -> None:
    if provider not in VALID_PROVIDERS:
        raise InvalidProviderError(
            f"Unknown provider {provider!r}. Valid: {VALID_PROVIDERS}"
        )
    if tier not in VALID_TIERS:
        raise InvalidTierError(f"Unknown tier {tier!r}. Valid: {VALID_TIERS}")


def _default_provider() -> str:
    """Return the first provider whose API key is present for this request.

    Resolution order: XAI_API_KEY -> OPENAI_API_KEY -> GEMINI_API_KEY.

    Single-user / stdio path: reads ``os.environ`` (credentials saved via the
    relay form / config.enc are written back into ``os.environ`` by
    ``imagine_mcp.relay_setup.apply_config``).

    HTTP multi-user path (``auth_scope`` middleware sets ``_current_sub``):
        Reads the per-sub config from ``~/.imagine-mcp/subs/<sub>/config.json``.
        ``os.environ`` is intentionally NOT consulted -- isolating users is
        the whole point of multi-user mode.

    Raises:
        CredentialMissingError: when no provider key is configured for the
        current request scope.
    """
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


def _load_provider(provider: str) -> Any:
    return importlib.import_module(f"imagine_mcp.providers.{provider}")


def _unsupported(provider: str, media: str, action: str) -> ProviderUnsupportedError:
    hint = _UNSUPPORTED_HINTS.get((provider, media, action), "")
    msg = f"{provider} does not support {action}.{media}."
    if hint:
        msg += " " + hint
    return ProviderUnsupportedError(msg)


def _process_url(index: int, url: str) -> str:
    """Validate and detect media type for a single URL concurrently."""
    _validate_url(url, f"media_urls[{index}]")
    return detect_media_type(url)


def dispatch_understand(
    media_urls: list[str],
    prompt: str,
    provider: str | None,
    tier: str,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """Dispatch understand call to provider.

    When ``provider`` is ``None``, auto-resolve via :func:`_default_provider`
    (first provider whose API key is present in the environment).
    """
    if provider is None:
        provider = _default_provider()
    _validate(provider, tier)
    if not media_urls:
        raise InvalidMediaTypeError("media_urls is empty")

    # Run validation and media type detection concurrently to avoid redundant sequential network calls
    # Iterating the results map preserves sequential exception propagation behavior.
    media_types = list(
        _DISPATCH_POOL.map(_process_url, range(len(media_urls)), media_urls)
    )

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
    provider: str | None,
    tier: str,
    reference_image_url: str | None = None,
    job_id: str | None = None,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
) -> dict[str, Any]:
    """Dispatch generate call to provider.

    When ``provider`` is ``None``, auto-resolve via :func:`_default_provider`
    (first provider whose API key is present in the environment).
    """
    if provider is None:
        provider = _default_provider()
    _validate(provider, tier)
    if media_type not in VALID_MEDIA_TYPES:
        raise InvalidMediaTypeError(
            f"Unknown media_type {media_type!r}. Valid: {VALID_MEDIA_TYPES}"
        )
    if reference_image_url is not None:
        _validate_url(reference_image_url, "reference_image_url")

    model = get_model_id(provider, "generate", media_type, tier)
    if model is UNSUPPORTED:
        raise _unsupported(provider, media_type, "generate")

    mod = _load_provider(provider)
    if media_type == "image":
        return mod.generate_image(prompt, tier, reference_image_url, aspect_ratio)
    return mod.generate_video(
        prompt, tier, reference_image_url, job_id, aspect_ratio, duration_seconds
    )
