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
    InvalidURLError,
    ProviderUnsupportedError,
)
from imagine_mcp.providers.base import GenerateParams, ImageParams


@pytest.fixture
def clean_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no provider API key is leaking from the host environment."""
    for var in ("XAI_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(var, raising=False)


def test_understand_routes_to_gemini_image(monkeypatch: pytest.MonkeyPatch) -> None:
    # Stub provider
    def mock_fn(url: str, prompt: str, tier: str, max_tokens: int = 2048) -> dict:
        return {"text": "stub", "model": "stub-model", "provider": "gemini"}

    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "understand_image", mock_fn)

    res = dispatch_understand(["http://example.com/i.png"], "hi", "gemini", "poor")
    assert res["provider"] == "gemini"


def test_understand_routes_to_gemini_video(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_fn(url: str, prompt: str, tier: str, max_tokens: int = 2048) -> dict:
        return {"text": "stub", "model": "stub-model", "provider": "gemini"}

    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "understand_video", mock_fn)

    res = dispatch_understand(["http://example.com/v.mp4"], "hi", "gemini", "poor")
    assert res["provider"] == "gemini"


def test_understand_multimodal_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_fn(
        urls: list[str],
        prompt: str,
        tier: str,
        max_tokens: int = 2048,
        media_types: list[str] | None = None,
    ) -> dict:
        return {"text": "stub", "multimodal": True, "provider": "gemini"}

    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "understand_multimodal", mock_fn)

    res = dispatch_understand(
        ["http://example.com/1.png", "http://example.com/2.mp4"], "hi", "gemini", "poor"
    )
    assert res["multimodal"] is True


def test_understand_unsupported_video_openai() -> None:
    with pytest.raises(ProviderUnsupportedError) as exc_info:
        dispatch_understand(["http://example.com/v.mp4"], "hi", "openai", "poor")
    assert "image-only" in str(exc_info.value)


def test_understand_unsupported_video_grok() -> None:
    with pytest.raises(ProviderUnsupportedError) as exc_info:
        dispatch_understand(["http://example.com/v.mp4"], "hi", "grok", "poor")
    assert "image-only" in str(exc_info.value)


def test_generate_invalid_media_type() -> None:
    with pytest.raises(InvalidMediaTypeError):
        dispatch_generate(
            GenerateParams(
                media_type="audio",
                prompt="hi",
                provider="gemini",
                tier="poor",
            )
        )


def test_generate_unsupported_video_openai() -> None:
    with pytest.raises(ProviderUnsupportedError) as exc_info:
        dispatch_generate(
            GenerateParams(
                media_type="video",
                prompt="a dog running",
                provider="openai",
                tier="poor",
            )
        )
    assert "Sora 2 API" in str(exc_info.value)


def test_dispatch_understand_rejects_non_http() -> None:
    with pytest.raises(InvalidURLError):
        dispatch_understand(["ftp://evil.com"], "hi", "gemini", "poor")


def test_dispatch_understand_rejects_internal_ip() -> None:
    # 127.0.0.1 is blocked by default
    with pytest.raises(InvalidURLError):
        dispatch_understand(["http://127.0.0.1/pwn"], "hi", "gemini", "poor")


def test_generate_rejects_non_http_reference_image_url() -> None:
    with pytest.raises(InvalidURLError, match="reference_image_url"):
        dispatch_generate(
            GenerateParams(
                media_type="image",
                prompt="cat",
                provider="gemini",
                tier="poor",
                reference_image_url="file:///etc/passwd",
            )
        )


def test_default_provider_raises_if_no_keys(clean_provider_env: None) -> None:
    with pytest.raises(CredentialMissingError):
        _default_provider()


def test_default_provider_resolves_grok(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XAI_API_KEY", "sk-grok")
    assert _default_provider() == "grok"


def test_default_provider_resolves_openai_if_grok_missing(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-oa")
    assert _default_provider() == "openai"


def test_default_provider_resolves_gemini_as_fallback(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "sk-gem")
    assert _default_provider() == "gemini"


def test_dispatch_generate_resolves_default_provider(
    clean_provider_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    captured: dict[str, str] = {}

    def mock_fn(params: ImageParams) -> dict:
        captured["called"] = "openai"
        return {"image": "...", "model": "gpt-image", "provider": "openai"}

    import imagine_mcp.providers.openai as openai_mod

    monkeypatch.setattr(openai_mod, "generate_image", mock_fn, raising=False)

    result = dispatch_generate(
        GenerateParams(
            media_type="image",
            prompt="a cat",
            provider=None,
            tier="poor",
        )
    )
    assert result["provider"] == "openai"
    assert captured["called"] == "openai"


def test_dispatch_understand_rejects_empty_list() -> None:
    with pytest.raises(InvalidMediaTypeError, match="empty"):
        dispatch_understand([], "hi", "gemini", "poor")
