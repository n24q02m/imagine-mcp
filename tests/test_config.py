from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from imagine_mcp.config import Settings


def test_default_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_AI_STUDIO_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    s = Settings()
    assert s.google_ai_studio_api_key is None
    assert s.openai_api_key is None
    assert s.xai_api_key is None
    assert s.log_level == "INFO"
    assert s.cache_ttl_seconds == 3600
    assert s.default_provider == "gemini"
    assert s.default_tier == "poor"
    assert s.poll_timeout_seconds == 300


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_AI_STUDIO_API_KEY", "test-key-123")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    s = Settings()
    assert s.google_ai_studio_api_key == "test-key-123"
    assert s.log_level == "DEBUG"


def test_invalid_log_level_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    with pytest.raises(PydanticValidationError):
        Settings()
