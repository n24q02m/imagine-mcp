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
    ProviderUnsupportedError,
)


@pytest.fixture
def clean_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no provider API key is leaking from the host environment."""
    for var in ("XAI_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(var, raising=False)


@pytest.mark.asyncio
async def test_understand_routes_to_gemini_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Stub provider
    async def mock_fn(url: str, prompt: str, tier: str, max_tokens: int = 2048) -> dict:
        return {"text": "a cat", "model": "gemini-x", "provider": "gemini"}

    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "understand_image", mock_fn, raising=False)
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type_async",
        AsyncMock(return_value="image"),
    )

    result = await dispatch_understand(
        media_urls=["https://example.com/cat.png"],
        prompt="describe",
        provider="gemini",
        tier="poor",
    )
    assert result["text"] == "a cat"


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
async def test_dispatch_understand_resolves_default_provider(
    clean_provider_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    captured: dict[str, str] = {}

    async def mock_fn(url: str, prompt: str, tier: str, max_tokens: int = 2048) -> dict:
        captured["called"] = "grok"
        return {"text": "ok", "model": "grok-x", "provider": "grok"}

    import imagine_mcp.providers.grok as grok_mod

    monkeypatch.setattr(grok_mod, "understand_image", mock_fn, raising=False)
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type_async",
        AsyncMock(return_value="image"),
    )

    result = await dispatch_understand(
        media_urls=["https://example.com/cat.png"],
        prompt="describe",
        provider=None,
        tier="poor",
    )
    assert captured["called"] == "grok"
    assert result["provider"] == "grok"


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
    mock_resp.content = b"fake-image-bytes"
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
    mock_resp.content = b"x"
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
    mock_resp.content = b"x"
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
    mock_resp.content = b"x"
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
async def test_dispatch_understand_explicit_provider_ignores_chain(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicit provider preserves the catalog path even with a chain set."""
    monkeypatch.setenv("UNDERSTAND_MODELS", "xai/grok-4.20-0309-non-reasoning")

    async def mock_fn(url: str, prompt: str, tier: str, max_tokens: int = 2048) -> dict:
        return {"text": "a cat", "model": "gemini-x", "provider": "gemini"}

    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "understand_image", mock_fn, raising=False)
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type_async",
        AsyncMock(return_value="image"),
    )

    result = await dispatch_understand(
        media_urls=["https://example.com/cat.png"],
        prompt="describe",
        provider="gemini",
        tier="poor",
    )
    # Catalog path, NOT passthrough chain.
    assert result["provider"] == "gemini"


@pytest.mark.asyncio
async def test_validate_url_blocks_cgnat() -> None:
    from imagine_mcp.dispatcher import _validate_url

    # 100.64.0.1 is part of Carrier-Grade NAT, which is not considered private by is_private,
    # but is considered not global by is_global. Our updated validation must block it.
    with pytest.raises(InvalidURLError, match="URL resolves to an internal/private IP"):
        await _validate_url("http://100.64.0.1/test", "test_param")
