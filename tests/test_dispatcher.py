from __future__ import annotations

import os
from unittest.mock import AsyncMock

import pytest

from imagine_mcp.dispatcher import (
    _default_provider,
    dispatch_generate,
    dispatch_understand,
    resolve_understand_chain,
)
from imagine_mcp.errors import (
    CredentialMissingError,
    InvalidMediaTypeError,
    InvalidProviderError,
    InvalidTierError,
    InvalidURLError,
    ModelNotConfiguredError,
    ProviderUnsupportedError,
)

# Minimal genuine image body: the 8-byte PNG signature is enough for the
# understand fetch path's magic-byte guard (``sniff_image_mime``) to accept it
# as image/png. Used as a stand-in for a real downloaded image so the mocked
# fetch represents genuine image bytes rather than an arbitrary placeholder.
_PNG_BYTES = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def clean_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no provider API key is leaking from the host environment."""
    for var in ("XAI_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(var, raising=False)


@pytest.mark.asyncio
async def test_understand_no_model_no_chain_raises(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#461: no explicit model + no UNDERSTAND_MODELS chain -> fail loud.

    Previously this silently fell back to a hardcoded leaderboard model_id
    (catalog default) for the given provider/tier. The catalog is gone: an
    arbitrary/custom model must be passed straight to litellm via `model=`
    or `UNDERSTAND_MODELS`, never silently substituted.
    """
    monkeypatch.delenv("UNDERSTAND_MODELS", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gem-test")

    with pytest.raises(ModelNotConfiguredError, match="UNDERSTAND_MODELS"):
        await dispatch_understand(
            media_urls=["https://example.com/cat.png"],
            prompt="describe",
            provider="gemini",
            tier="poor",
        )


@pytest.mark.asyncio
async def test_understand_invalid_provider() -> None:
    with pytest.raises(InvalidProviderError):
        await dispatch_understand(
            media_urls=["https://example.com/x.png"],
            prompt="hi",
            provider="unknown",
            tier="poor",
        )


@pytest.mark.asyncio
async def test_understand_invalid_tier() -> None:
    with pytest.raises(InvalidTierError):
        await dispatch_understand(
            media_urls=["https://example.com/x.png"],
            prompt="hi",
            provider="gemini",
            tier="mega",
        )


@pytest.mark.asyncio
async def test_understand_unsupported_video_openai(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type_async",
        AsyncMock(return_value="video"),
    )
    with pytest.raises(ProviderUnsupportedError) as exc_info:
        await dispatch_understand(
            media_urls=["https://example.com/x.mp4"],
            prompt="hi",
            provider="openai",
            tier="poor",
        )
    assert "video" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_understand_unsupported_video_grok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type_async",
        AsyncMock(return_value="video"),
    )
    with pytest.raises(ProviderUnsupportedError):
        await dispatch_understand(
            media_urls=["https://example.com/x.mp4"],
            prompt="hi",
            provider="grok",
            tier="rich",
        )


@pytest.mark.asyncio
async def test_generate_invalid_media_type() -> None:
    with pytest.raises(InvalidMediaTypeError):
        await dispatch_generate(
            media_type="audio",
            prompt="hi",
            provider="gemini",
            tier="poor",
        )


@pytest.mark.asyncio
async def test_generate_unsupported_video_openai() -> None:
    with pytest.raises(ProviderUnsupportedError) as exc_info:
        await dispatch_generate(
            media_type="video",
            prompt="a dog running",
            provider="openai",
            tier="poor",
        )
    assert (
        "sora" in str(exc_info.value).lower()
        or "shutdown" in str(exc_info.value).lower()
    )


@pytest.mark.parametrize(
    "bad_url",
    [
        "file:///etc/passwd",
        "ftp://internal.local/secret",
        "gopher://127.0.0.1:9000/_x",
        "//no-scheme.example.com/a.png",
        "javascript:alert(1)",
        "http://localhost",
        "http://127.0.0.1",
        "https://127.0.0.1",
        "http://169.254.169.254",
        "http://0x7f000001",
        "http://0.0.0.0",
        "http://10.0.0.1",
        "https://192.168.1.5",
        "http://[::ffff:127.0.0.1]/",
        "http://[::ffff:7f00:1]/",
    ],
)
@pytest.mark.asyncio
async def test_understand_rejects_non_http_url(bad_url: str) -> None:
    with pytest.raises(InvalidURLError):
        await dispatch_understand(
            media_urls=[bad_url],
            prompt="hi",
            provider="gemini",
            tier="poor",
        )


@pytest.mark.asyncio
async def test_understand_rejects_non_http_url_in_second_position() -> None:
    with pytest.raises(InvalidURLError, match=r"media_urls\[1\]"):
        await dispatch_understand(
            media_urls=["https://example.com/ok.png", "file:///etc/passwd"],
            prompt="hi",
            provider="gemini",
            tier="poor",
        )


@pytest.mark.asyncio
async def test_generate_rejects_non_http_reference_image_url() -> None:
    with pytest.raises(InvalidURLError, match="reference_image_url"):
        await dispatch_generate(
            media_type="image",
            prompt="cat",
            provider="gemini",
            tier="poor",
            reference_image_url="file:///etc/passwd",
        )


def test_default_provider_grok_only(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    assert _default_provider() == "grok"


def test_default_provider_openai_only(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert _default_provider() == "openai"


def test_default_provider_priority_grok_over_openai(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert _default_provider() == "grok"


def test_default_provider_gemini_last_resort(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gem-test")
    assert _default_provider() == "gemini"


def test_default_provider_priority_openai_over_gemini(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("GEMINI_API_KEY", "gem-test")
    assert _default_provider() == "openai"


def test_default_provider_raises_when_none_set(clean_provider_env: None) -> None:
    with pytest.raises(CredentialMissingError) as exc_info:
        _default_provider()
    msg = str(exc_info.value)
    assert "XAI_API_KEY" in msg
    assert "OPENAI_API_KEY" in msg
    assert "GEMINI_API_KEY" in msg


@pytest.mark.asyncio
async def test_dispatch_understand_no_model_names_default_provider_in_error(
    clean_provider_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No model/chain + no explicit provider -> error names the auto-resolved
    provider (the auto-fallback still runs; it just no longer picks a model)."""
    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type_async",
        AsyncMock(return_value="image"),
    )

    with pytest.raises(ModelNotConfiguredError, match="provider='grok'"):
        await dispatch_understand(
            media_urls=["https://example.com/cat.png"],
            prompt="describe",
            provider=None,
            tier="poor",
        )


@pytest.mark.asyncio
async def test_dispatch_generate_resolves_default_provider(
    clean_provider_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    captured: dict[str, str] = {}

    async def mock_fn(
        prompt: str,
        tier: str,
        reference_image_url: str | None,
        aspect_ratio: str,
        output_mode: str = "both",
        model_id: str | None = None,
    ) -> dict:
        captured["called"] = "openai"
        return {"image": "...", "model": "gpt-image", "provider": "openai"}

    import imagine_mcp.providers.openai as openai_mod

    monkeypatch.setattr(openai_mod, "generate_image", mock_fn, raising=False)

    result = await dispatch_generate(
        media_type="image",
        prompt="a cat",
        provider=None,
        tier="poor",
    )
    assert captured["called"] == "openai"
    assert result["provider"] == "openai"


@pytest.mark.asyncio
async def test_dispatch_understand_no_keys_raises_credential_missing(
    clean_provider_env: None,
) -> None:
    with pytest.raises(CredentialMissingError):
        await dispatch_understand(
            media_urls=["https://example.com/cat.png"],
            prompt="describe",
            provider=None,
            tier="poor",
        )


@pytest.mark.asyncio
async def test_understand_rejects_dns_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    import time

    def mock_getaddrinfo(*args, **kwargs):
        time.sleep(3)
        return []

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo)

    start = time.time()
    with pytest.raises(InvalidURLError, match=r"timed out for 'slow\.example\.com'"):
        await dispatch_understand(
            media_urls=["http://slow.example.com/test.png"],
            prompt="hi",
            provider="gemini",
            tier="poor",
        )
    duration = time.time() - start
    assert duration < 2.5, f"DNS timeout block took too long: {duration}s"


@pytest.mark.asyncio
async def test_passthrough_understand_routes_to_litellm(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicit ``model`` bypasses the catalog and calls litellm directly."""
    from unittest.mock import MagicMock

    monkeypatch.setenv("GEMINI_API_KEY", "gem-test")

    msg = MagicMock()
    msg.content = "a passthrough cat"
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]

    captured: dict[str, object] = {}

    async def fake_acompletion(**kwargs: object) -> object:
        captured.update(kwargs)
        return resp

    monkeypatch.setattr("mcp_core.llm.acompletion", fake_acompletion)
    # Avoid real image download.
    mock_resp = MagicMock()
    mock_resp.content = _PNG_BYTES
    mock_resp.headers = {"content-type": "image/png"}
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )

    result = await dispatch_understand(
        media_urls=["https://example.com/cat.png"],
        prompt="describe",
        provider=None,
        tier="poor",
        model="gemini/gemini-3.1-pro-preview",
    )
    assert result["text"] == "a passthrough cat"
    assert result["provider"] == "passthrough"
    assert result["model"] == "gemini/gemini-3.1-pro-preview"
    assert captured["model"] == "gemini/gemini-3.1-pro-preview"
    assert captured["api_key"] == "gem-test"


@pytest.mark.asyncio
async def test_passthrough_understand_unknown_model_warns(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A registry-missing model passes through with a warning field."""
    from unittest.mock import MagicMock

    msg = MagicMock()
    msg.content = "ok"
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]

    async def fake_acompletion(**kwargs: object) -> object:
        return resp

    monkeypatch.setattr("mcp_core.llm.acompletion", fake_acompletion)
    mock_resp = MagicMock()
    mock_resp.content = _PNG_BYTES
    mock_resp.headers = {"content-type": "image/png"}
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )

    result = await dispatch_understand(
        media_urls=["https://example.com/cat.png"],
        prompt="describe",
        provider=None,
        tier="poor",
        model="acme/never-heard-of-it",
    )
    assert "warning" in result
    assert "registry" in result["warning"]


@pytest.mark.asyncio
async def test_passthrough_understand_capability_mismatch_raises(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A known model with the wrong mode is surfaced as ProviderUnsupportedError."""
    from mcp_core.llm import ModelCapabilityError

    def fake_check_capability(model: str, modes: tuple[str, ...]) -> None:
        raise ModelCapabilityError(
            f"model {model!r} has mode='image_generation', expected one of {modes}."
        )

    # Patch at the resolution site (lazy `from mcp_core.llm import check_capability`).
    monkeypatch.setattr("mcp_core.llm.check_capability", fake_check_capability)
    # Capability check precedes image download; stub URL validation so the test
    # does not depend on DNS resolution.
    monkeypatch.setattr(
        "imagine_mcp.dispatcher._validate_url", AsyncMock(return_value=None)
    )

    with pytest.raises(ProviderUnsupportedError, match="expected one of"):
        await dispatch_understand(
            media_urls=["https://example.com/cat.png"],
            prompt="describe",
            provider=None,
            tier="poor",
            model="gemini/gemini-3.1-flash-image-preview",
        )


@pytest.mark.asyncio
async def test_passthrough_generate_xai_routes_native_grok(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An xai/ model on generate resolves to the native grok provider."""
    captured: dict[str, str] = {}

    async def mock_fn(
        prompt: str,
        tier: str,
        reference_image_url: str | None,
        aspect_ratio: str,
        output_mode: str = "both",
        model_id: str | None = None,
    ) -> dict:
        captured["called"] = "grok"
        return {"image": "...", "model": "grok-imagine-image", "provider": "grok"}

    import imagine_mcp.providers.grok as grok_mod

    monkeypatch.setattr(grok_mod, "generate_image", mock_fn, raising=False)

    result = await dispatch_generate(
        media_type="image",
        prompt="a cat",
        provider=None,
        tier="poor",
        model="xai/grok-imagine-image",
    )
    assert captured["called"] == "grok"
    assert result["provider"] == "grok"


@pytest.mark.asyncio
async def test_passthrough_generate_unknown_prefix_raises_litellm_gap() -> None:
    """A generate model with an unmappable prefix returns the litellm-gap error."""
    with pytest.raises(ProviderUnsupportedError, match="litellm gap"):
        await dispatch_generate(
            media_type="image",
            prompt="a cat",
            provider=None,
            tier="poor",
            model="cohere/some-image-model",
        )


def test_understand_chain_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "UNDERSTAND_MODELS",
        "xai/grok-4.20-0309-non-reasoning,gemini/gemini-3.1-flash-lite-preview",
    )
    assert resolve_understand_chain()[0] == "xai/grok-4.20-0309-non-reasoning"


def test_understand_chain_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("UNDERSTAND_MODELS", raising=False)
    assert resolve_understand_chain() == []


def test_understand_chain_strips_and_skips_blanks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UNDERSTAND_MODELS", " xai/grok , , gemini/flash ,")
    assert resolve_understand_chain() == ["xai/grok", "gemini/flash"]


def test_understand_chain_blank_string_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UNDERSTAND_MODELS", "   ")
    assert resolve_understand_chain() == []
    # Sanity: env var is genuinely present (not absent) for this case.
    assert os.getenv("UNDERSTAND_MODELS") == "   "


@pytest.mark.asyncio
async def test_dispatch_understand_uses_chain_default(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No explicit model/provider + UNDERSTAND_MODELS set -> chain passthrough."""
    from unittest.mock import MagicMock

    monkeypatch.setenv(
        "UNDERSTAND_MODELS",
        "xai/grok-4.20-0309-non-reasoning,gemini/gemini-3.1-flash-lite-preview",
    )
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    msg = MagicMock()
    msg.content = "chain cat"
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]

    captured: dict[str, object] = {}

    async def fake_acompletion(**kwargs: object) -> object:
        captured.update(kwargs)
        return resp

    monkeypatch.setattr("mcp_core.llm.acompletion", fake_acompletion)
    mock_resp = MagicMock()
    mock_resp.content = _PNG_BYTES
    mock_resp.headers = {"content-type": "image/png"}
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )

    result = await dispatch_understand(
        media_urls=["https://example.com/cat.png"],
        prompt="describe",
        provider=None,
        tier="poor",
    )
    assert result["provider"] == "passthrough"
    assert captured["model"] == "xai/grok-4.20-0309-non-reasoning"
    assert captured["fallbacks"] == ["gemini/gemini-3.1-flash-lite-preview"]


@pytest.mark.asyncio
async def test_dispatch_understand_single_chain_no_fallbacks(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A one-entry chain forwards fallbacks=None (no empty-list noise)."""
    from unittest.mock import MagicMock

    monkeypatch.setenv("UNDERSTAND_MODELS", "xai/grok-4.20-0309-non-reasoning")
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    msg = MagicMock()
    msg.content = "ok"
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]

    captured: dict[str, object] = {}

    async def fake_acompletion(**kwargs: object) -> object:
        captured.update(kwargs)
        return resp

    monkeypatch.setattr("mcp_core.llm.acompletion", fake_acompletion)
    mock_resp = MagicMock()
    mock_resp.content = _PNG_BYTES
    mock_resp.headers = {"content-type": "image/png"}
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )

    result = await dispatch_understand(
        media_urls=["https://example.com/cat.png"],
        prompt="describe",
        provider=None,
        tier="poor",
    )
    assert result["model"] == "xai/grok-4.20-0309-non-reasoning"
    assert captured["fallbacks"] is None


@pytest.mark.asyncio
async def test_dispatch_understand_explicit_provider_does_not_override_chain(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#461: there is no per-provider catalog path to fall back to any more, so an
    explicit ``provider`` (used only for validation / video-capability gating) does
    NOT override the ``UNDERSTAND_MODELS`` chain -- the chain is still the only
    source of the model, exactly as when ``provider`` is omitted."""
    from unittest.mock import MagicMock

    monkeypatch.setenv("UNDERSTAND_MODELS", "xai/grok-4.20-0309-non-reasoning")

    msg = MagicMock()
    msg.content = "a cat"
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]

    async def fake_acompletion(**kwargs: object) -> object:
        return resp

    monkeypatch.setattr("mcp_core.llm.acompletion", fake_acompletion)
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type_async",
        AsyncMock(return_value="image"),
    )
    mock_resp = MagicMock()
    mock_resp.content = _PNG_BYTES
    mock_resp.headers = {"content-type": "image/png"}
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )

    result = await dispatch_understand(
        media_urls=["https://example.com/cat.png"],
        prompt="describe",
        provider="gemini",
        tier="poor",
    )
    # Chain passthrough, not a gemini-specific route -- ``provider`` did not
    # steer model resolution.
    assert result["provider"] == "passthrough"
    assert result["model"] == "xai/grok-4.20-0309-non-reasoning"


@pytest.mark.asyncio
async def test_validate_url_blocks_cgnat() -> None:
    from imagine_mcp.dispatcher import _validate_url

    # 100.64.0.1 is part of Carrier-Grade NAT, which is not considered private by is_private,
    # but is considered not global by is_global. Our updated validation must block it.
    with pytest.raises(InvalidURLError, match="URL resolves to an internal/private IP"):
        await _validate_url("http://100.64.0.1/test", "test_param")


@pytest.mark.asyncio
async def test_validate_url_success(monkeypatch: pytest.MonkeyPatch) -> None:
    from imagine_mcp.dispatcher import _validate_url

    def mock_validate(url: str, param: str) -> str:
        return "1.1.1.1"

    monkeypatch.setattr("imagine_mcp.dispatcher.validate_url_and_get_ip", mock_validate)

    # Should not raise
    await _validate_url("https://example.com/image.png", "test_param")


@pytest.mark.asyncio
async def test_validate_url_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    from imagine_mcp.dispatcher import _validate_url

    def mock_validate(url: str, param: str) -> str:
        raise InvalidURLError("mocked failure")

    monkeypatch.setattr("imagine_mcp.dispatcher.validate_url_and_get_ip", mock_validate)

    with pytest.raises(InvalidURLError, match="mocked failure"):
        await _validate_url("https://example.com/image.png", "test_param")


def test_validate_invalid_provider() -> None:
    from imagine_mcp.dispatcher import _validate

    with pytest.raises(InvalidProviderError, match="Unknown provider"):
        _validate("invalid-provider", "poor")


def test_validate_invalid_tier() -> None:
    from imagine_mcp.dispatcher import _validate

    with pytest.raises(InvalidTierError, match="Unknown tier"):
        _validate("gemini", "invalid-tier")


@pytest.mark.asyncio
async def test_passthrough_understand_raises_on_http_error(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-2xx media fetch (e.g. Wikimedia 403 "Please set a user agent") is
    surfaced loudly. The error body must never be base64'd and handed to the
    vision model as if it were an image (silent failure -> confident garbage).
    """
    from unittest.mock import MagicMock

    import httpx

    monkeypatch.setenv("GEMINI_API_KEY", "gem-test")
    monkeypatch.setattr(
        "imagine_mcp.dispatcher._validate_url", AsyncMock(return_value=None)
    )

    acompletion_calls: list[dict[str, object]] = []

    async def fake_acompletion(**kwargs: object) -> object:
        acompletion_calls.append(kwargs)
        benign = MagicMock()
        benign.choices = [MagicMock()]
        return benign

    monkeypatch.setattr("mcp_core.llm.acompletion", fake_acompletion)

    error_resp = MagicMock()
    error_resp.status_code = 403
    error_resp.content = b"Please set a user agent"
    error_resp.headers = {"content-type": "text/plain"}
    error_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "403 Forbidden", request=MagicMock(), response=MagicMock()
    )
    mock_client = AsyncMock()
    mock_client.get.return_value = error_resp
    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )

    with pytest.raises(httpx.HTTPStatusError):
        await dispatch_understand(
            media_urls=["https://upload.wikimedia.org/cat.jpg"],
            prompt="describe",
            provider=None,
            tier="poor",
            model="gemini/gemini-3.1-pro-preview",
        )
    assert acompletion_calls == [], "vision model called on a failed fetch"


@pytest.mark.asyncio
async def test_passthrough_understand_rejects_non_image_body(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 200 response whose body is not an image (HTML/text error page with no
    image magic bytes) is rejected with a clear error -- not base64'd and sent
    to the vision model."""
    from unittest.mock import MagicMock

    monkeypatch.setenv("GEMINI_API_KEY", "gem-test")
    monkeypatch.setattr(
        "imagine_mcp.dispatcher._validate_url", AsyncMock(return_value=None)
    )

    acompletion_calls: list[dict[str, object]] = []

    async def fake_acompletion(**kwargs: object) -> object:
        acompletion_calls.append(kwargs)
        benign = MagicMock()
        benign.choices = [MagicMock()]
        return benign

    monkeypatch.setattr("mcp_core.llm.acompletion", fake_acompletion)

    html_resp = MagicMock()
    html_resp.status_code = 200
    html_resp.content = b"<!DOCTYPE html><html><body>Rate limited</body></html>"
    html_resp.headers = {"content-type": "text/html"}
    html_resp.raise_for_status = MagicMock(return_value=None)
    mock_client = AsyncMock()
    mock_client.get.return_value = html_resp
    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )

    with pytest.raises(InvalidMediaTypeError, match="image"):
        await dispatch_understand(
            media_urls=["https://example.com/notreally.png"],
            prompt="describe",
            provider=None,
            tier="poor",
            model="gemini/gemini-3.1-pro-preview",
        )
    assert acompletion_calls == [], "vision model called on a non-image body"


@pytest.mark.asyncio
async def test_passthrough_understand_accepts_real_image(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 200 response with genuine image magic bytes proceeds normally; the data
    URL mime is derived from the sniffed magic bytes and litellm is called."""
    from unittest.mock import MagicMock

    monkeypatch.setenv("GEMINI_API_KEY", "gem-test")
    monkeypatch.setattr(
        "imagine_mcp.dispatcher._validate_url", AsyncMock(return_value=None)
    )

    msg = MagicMock()
    msg.content = "a real cat"
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]

    captured: dict[str, object] = {}

    async def fake_acompletion(**kwargs: object) -> object:
        captured.update(kwargs)
        return resp

    monkeypatch.setattr("mcp_core.llm.acompletion", fake_acompletion)

    img_resp = MagicMock()
    img_resp.status_code = 200
    img_resp.content = _PNG_BYTES
    # A lying/generic content-type must not steer the mime: magic bytes win.
    img_resp.headers = {"content-type": "application/octet-stream"}
    img_resp.raise_for_status = MagicMock(return_value=None)
    mock_client = AsyncMock()
    mock_client.get.return_value = img_resp
    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )

    result = await dispatch_understand(
        media_urls=["https://example.com/cat.png"],
        prompt="describe",
        provider=None,
        tier="poor",
        model="gemini/gemini-3.1-pro-preview",
    )
    assert result["text"] == "a real cat"
    from typing import Any, cast

    messages = cast(list[dict[str, Any]], captured["messages"])
    content = messages[0]["content"]
    image_parts = [part for part in content if part.get("type") == "image_url"]
    assert image_parts, "expected an image_url part in the vision message"
    assert image_parts[0]["image_url"]["url"].startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_passthrough_understand_sends_user_agent(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The media fetch sends a real, identifying User-Agent header -- many hosts
    (e.g. Wikimedia) 403 a request that carries no/blank UA."""
    from unittest.mock import MagicMock

    monkeypatch.setenv("GEMINI_API_KEY", "gem-test")
    monkeypatch.setattr(
        "imagine_mcp.dispatcher._validate_url", AsyncMock(return_value=None)
    )

    msg = MagicMock()
    msg.content = "ok"
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]

    async def fake_acompletion(**kwargs: object) -> object:
        return resp

    monkeypatch.setattr("mcp_core.llm.acompletion", fake_acompletion)

    img_resp = MagicMock()
    img_resp.status_code = 200
    img_resp.content = _PNG_BYTES
    img_resp.headers = {"content-type": "image/png"}
    img_resp.raise_for_status = MagicMock(return_value=None)
    mock_client = AsyncMock()
    mock_client.get.return_value = img_resp
    monkeypatch.setattr(
        "imagine_mcp.media.get_ssrf_safe_async_client", lambda: mock_client
    )

    await dispatch_understand(
        media_urls=["https://example.com/cat.png"],
        prompt="describe",
        provider=None,
        tier="poor",
        model="gemini/gemini-3.1-pro-preview",
    )
    _args, kwargs = mock_client.get.call_args
    headers = kwargs.get("headers") or {}
    user_agent = headers.get("User-Agent", "")
    assert user_agent, "media fetch must send a non-empty User-Agent header"
    assert "imagine" in user_agent.lower()
