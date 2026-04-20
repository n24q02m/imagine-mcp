"""Tests for imagine-mcp mega-tool dispatch validation + routing."""
from __future__ import annotations
import pytest

from imagine_mcp.server import dispatch


def test_dispatch_routes_to_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict = {}

    def fake_understand(tier: str, image_url: str, prompt: str) -> dict:
        called["args"] = (tier, image_url, prompt)
        return {"text": "a cat", "model": "gemini-3.1-flash"}

    monkeypatch.setattr("imagine_mcp.providers.gemini.understand", fake_understand)

    result = dispatch(
        action="understand",
        provider="gemini",
        tier="poor",
        image_url="https://example.com/cat.png",
        prompt="describe",
    )
    assert called["args"] == ("poor", "https://example.com/cat.png", "describe")
    assert result["text"] == "a cat"


def test_dispatch_invalid_provider() -> None:
    with pytest.raises(ValueError, match="Unknown provider"):
        dispatch(action="understand", provider="unknown", tier="poor")


def test_dispatch_invalid_action() -> None:
    with pytest.raises(ValueError, match="Unknown action"):
        dispatch(action="invalid", provider="gemini", tier="poor")


def test_dispatch_invalid_tier() -> None:
    with pytest.raises(ValueError, match="Unknown tier"):
        dispatch(action="understand", provider="gemini", tier="mega")


def test_dispatch_stubbed_path_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        dispatch(
            action="generate",
            provider="openai",
            tier="rich",
            prompt="a watercolor fox",
        )


def test_dispatch_grok_understand_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        dispatch(
            action="understand",
            provider="grok",
            tier="rich",
            image_url="https://example.com/x.png",
            prompt="hi",
        )


def test_gemini_understand_ssrf_lfi_prevention() -> None:
    from imagine_mcp.providers.gemini import understand

    with pytest.raises(ValueError, match="Invalid image_url"):
        understand(
            tier="poor",
            image_url="file:///etc/passwd",
            prompt="describe",
        )
