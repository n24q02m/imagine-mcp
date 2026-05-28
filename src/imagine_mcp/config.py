"""Runtime configuration via pydantic-settings."""

from __future__ import annotations

from typing import Final, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Mapping of provider names to their respective API key environment variable names.
PROVIDER_TO_KEY: Final[dict[str, str]] = {
    "grok": "XAI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=None,  # Never load .env -- MCP server env comes from client config
        case_sensitive=False,
        extra="ignore",
    )

    # Credentials (all optional -- degraded mode if missing).
    # Renamed 2026-04-26: GOOGLE_AI_STUDIO_API_KEY -> GEMINI_API_KEY for parity
    # with wet/mnemo/crg.
    gemini_api_key: str | None = Field(default=None)
    openai_api_key: str | None = Field(default=None)
    xai_api_key: str | None = Field(default=None)

    # Runtime
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    cache_ttl_seconds: int = Field(default=3600, ge=0)
    default_provider: Literal["gemini", "openai", "grok"] = Field(default="gemini")
    default_tier: Literal["poor", "rich"] = Field(default="poor")
    poll_timeout_seconds: int = Field(default=300, ge=1, le=3600)
    max_media_urls: int = Field(default=5, ge=1, le=20)

    # Auto-fallback priority when caller does not pin a provider. Order is
    # (XAI, OpenAI, Gemini): Gemini stays last because Google AI Studio
    # accounts can be billing-locked at the org level (403 PERMISSION_DENIED
    # on every :generateContent call) without warning, so we prefer keys
    # that are less prone to silent revocation.
    provider_priority: list[str] = Field(default=["grok", "openai", "gemini"])


settings = Settings()
