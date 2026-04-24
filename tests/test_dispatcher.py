from __future__ import annotations

import pytest

from imagine_mcp.dispatcher import dispatch_generate, dispatch_understand
from imagine_mcp.errors import (
    InvalidMediaTypeError,
    InvalidProviderError,
    InvalidTierError,
    ProviderUnsupportedError,
)


def test_understand_routes_to_gemini_image(monkeypatch: pytest.MonkeyPatch) -> None:
    # Stub provider
    def mock_fn(url: str, prompt: str, tier: str, max_tokens: int = 2048) -> dict:
        return {"text": "a cat", "model": "gemini-x", "provider": "gemini"}

    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "understand_image", mock_fn, raising=False)
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type", lambda u: "image"
    )

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
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type", lambda u: "video"
    )
    with pytest.raises(ProviderUnsupportedError) as exc_info:
        dispatch_understand(
            media_urls=["https://example.com/x.mp4"],
            prompt="hi",
            provider="openai",
            tier="poor",
        )
    assert "video" in str(exc_info.value).lower()


def test_understand_unsupported_video_grok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type", lambda u: "video"
    )
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
    assert "sora" in str(exc_info.value).lower() or "shutdown" in str(exc_info.value).lower()
