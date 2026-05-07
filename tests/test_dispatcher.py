from __future__ import annotations

import pytest

from imagine_mcp.dispatcher import (
    _default_provider,
    dispatch_generate,
    dispatch_understand,
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


def test_understand_routes_to_gemini_image(monkeypatch: pytest.MonkeyPatch) -> None:
    # Stub provider
    def mock_fn(url: str, prompt: str, tier: str, max_tokens: int = 2048) -> dict:
        return {"text": "a cat", "model": "gemini-x", "provider": "gemini"}

    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "understand_image", mock_fn, raising=False)
    monkeypatch.setattr("imagine_mcp.dispatcher.detect_media_type", lambda u: "image")

    result = dispatch_understand(
        media_urls=["https://example.com/cat.png"],
        prompt="describe",
        provider="gemini",
        tier="poor",
    )
    assert result["text"] == "a cat"


def test_understand_invalid_provider() -> None:
    with pytest.raises(InvalidProviderError):
        dispatch_understand(
            media_urls=["https://example.com/x.png"],
            prompt="hi",
            provider="unknown",
            tier="poor",
        )


def test_understand_invalid_tier() -> None:
    with pytest.raises(InvalidTierError):
        dispatch_understand(
            media_urls=["https://example.com/x.png"],
            prompt="hi",
            provider="gemini",
            tier="mega",
        )


def test_understand_unsupported_video_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("imagine_mcp.dispatcher.detect_media_type", lambda u: "video")
    with pytest.raises(ProviderUnsupportedError) as exc_info:
        dispatch_understand(
            media_urls=["https://example.com/x.mp4"],
            prompt="hi",
            provider="openai",
            tier="poor",
        )
    assert "video" in str(exc_info.value).lower()


def test_understand_unsupported_video_grok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("imagine_mcp.dispatcher.detect_media_type", lambda u: "video")
    with pytest.raises(ProviderUnsupportedError):
        dispatch_understand(
            media_urls=["https://example.com/x.mp4"],
            prompt="hi",
            provider="grok",
            tier="rich",
        )


def test_generate_invalid_media_type() -> None:
    with pytest.raises(InvalidMediaTypeError):
        dispatch_generate(
            media_type="audio",
            prompt="hi",
            provider="gemini",
            tier="poor",
        )


def test_generate_unsupported_video_openai() -> None:
    with pytest.raises(ProviderUnsupportedError) as exc_info:
        dispatch_generate(
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
def test_understand_rejects_non_http_url(bad_url: str) -> None:
    with pytest.raises(InvalidURLError):
        dispatch_understand(
            media_urls=[bad_url],
            prompt="hi",
            provider="gemini",
            tier="poor",
        )


def test_understand_rejects_non_http_url_in_second_position() -> None:
    with pytest.raises(InvalidURLError, match=r"media_urls\[1\]"):
        dispatch_understand(
            media_urls=["https://example.com/ok.png", "file:///etc/passwd"],
            prompt="hi",
            provider="gemini",
            tier="poor",
        )


def test_generate_rejects_non_http_reference_image_url() -> None:
    with pytest.raises(InvalidURLError, match="reference_image_url"):
        dispatch_generate(
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


def test_dispatch_understand_resolves_default_provider(
    clean_provider_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    captured: dict[str, str] = {}

    def mock_fn(url: str, prompt: str, tier: str, max_tokens: int = 2048) -> dict:
        captured["called"] = "grok"
        return {"text": "ok", "model": "grok-x", "provider": "grok"}

    import imagine_mcp.providers.grok as grok_mod

    monkeypatch.setattr(grok_mod, "understand_image", mock_fn, raising=False)
    monkeypatch.setattr("imagine_mcp.dispatcher.detect_media_type", lambda u: "image")

    result = dispatch_understand(
        media_urls=["https://example.com/cat.png"],
        prompt="describe",
        provider=None,
        tier="poor",
    )
    assert captured["called"] == "grok"
    assert result["provider"] == "grok"


def test_dispatch_generate_resolves_default_provider(
    clean_provider_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    captured: dict[str, str] = {}

    def mock_fn(
        prompt: str,
        tier: str,
        reference_image_url: str | None,
        aspect_ratio: str,
    ) -> dict:
        captured["called"] = "openai"
        return {"image": "...", "model": "gpt-image", "provider": "openai"}

    import imagine_mcp.providers.openai as openai_mod

    monkeypatch.setattr(openai_mod, "generate_image", mock_fn, raising=False)

    result = dispatch_generate(
        media_type="image",
        prompt="a cat",
        provider=None,
        tier="poor",
    )
    assert captured["called"] == "openai"
    assert result["provider"] == "openai"


def test_dispatch_understand_no_keys_raises_credential_missing(
    clean_provider_env: None,
) -> None:
    with pytest.raises(CredentialMissingError):
        dispatch_understand(
            media_urls=["https://example.com/cat.png"],
            prompt="describe",
            provider=None,
            tier="poor",
        )


def test_understand_rejects_dns_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    import time

    def mock_getaddrinfo(*args, **kwargs):
        time.sleep(3)
        return []

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo)

    start = time.time()
    with pytest.raises(InvalidURLError, match=r"timed out for 'slow\.example\.com'"):
        dispatch_understand(
            media_urls=["http://slow.example.com/test.png"],
            prompt="hi",
            provider="gemini",
            tier="poor",
        )
    duration = time.time() - start
    assert duration < 2.5, f"DNS timeout block took too long: {duration}s"


def test_validate_url_blocks_cgnat() -> None:
    from imagine_mcp.dispatcher import _validate_url

    # 100.64.0.1 is part of Carrier-Grade NAT, which is not considered private by is_private,
    # but is considered not global by is_global. Our updated validation must block it.
    with pytest.raises(InvalidURLError, match="URL resolves to an internal/private IP"):
        _validate_url("http://100.64.0.1/test", "test_param")


def test_understand_parallel_validation_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Stub detect_media_type to avoid real network calls
    monkeypatch.setattr("imagine_mcp.dispatcher.detect_media_type", lambda u: "image")

    # Stub provider
    def mock_multimodal(
        urls: list[str], prompt: str, tier: str, max_tokens: int = 2048
    ) -> dict:
        return {"text": "ok", "provider": "gemini"}

    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(
        gemini_mod, "understand_multimodal", mock_multimodal, raising=False
    )

    # Use multiple valid URLs
    urls = [
        "https://example.com/1.png",
        "https://example.com/2.png",
        "https://example.com/3.png",
    ]

    result = dispatch_understand(
        media_urls=urls, prompt="describe", provider="gemini", tier="poor"
    )
    assert result["provider"] == "gemini"


def test_understand_parallel_validation_error_propagation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Stub detect_media_type
    monkeypatch.setattr("imagine_mcp.dispatcher.detect_media_type", lambda u: "image")

    # One invalid URL among valid ones
    urls = [
        "https://example.com/1.png",
        "file:///etc/passwd",
        "https://example.com/3.png",
    ]

    with pytest.raises(InvalidURLError, match=r"media_urls\[1\]"):
        dispatch_understand(
            media_urls=urls, prompt="describe", provider="gemini", tier="poor"
        )
