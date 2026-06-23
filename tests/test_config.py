from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from imagine_mcp.config import Settings


def test_default_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    # Clear all environment variables that could influence Settings
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("UNDERSTAND_MODELS", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("CACHE_TTL_SECONDS", raising=False)
    monkeypatch.delenv("DEFAULT_PROVIDER", raising=False)
    monkeypatch.delenv("DEFAULT_TIER", raising=False)
    monkeypatch.delenv("POLL_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("MAX_MEDIA_URLS", raising=False)

    s = Settings()
    assert s.gemini_api_key is None
    assert s.openai_api_key is None
    assert s.xai_api_key is None
    assert s.understand_models is None
    assert s.log_level == "INFO"
    assert s.cache_ttl_seconds == 3600
    assert s.default_provider == "gemini"
    assert s.default_tier == "poor"
    assert s.poll_timeout_seconds == 300
    assert s.max_media_urls == 5


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MAX_MEDIA_URLS", "10")
    s = Settings()
    assert s.gemini_api_key == "test-key-123"
    assert s.log_level == "DEBUG"
    assert s.max_media_urls == 10


def test_invalid_log_level_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    with pytest.raises(PydanticValidationError):
        Settings()


def test_settings_constraints() -> None:
    # Verify cache_ttl_seconds ge=0
    with pytest.raises(PydanticValidationError):
        Settings(cache_ttl_seconds=-1)

    # Verify poll_timeout_seconds ge=1 and le=3600
    with pytest.raises(PydanticValidationError):
        Settings(poll_timeout_seconds=0)
    with pytest.raises(PydanticValidationError):
        Settings(poll_timeout_seconds=3601)

    # Verify max_media_urls ge=1 and le=20
    with pytest.raises(PydanticValidationError):
        Settings(max_media_urls=0)
    with pytest.raises(PydanticValidationError):
        Settings(max_media_urls=21)
