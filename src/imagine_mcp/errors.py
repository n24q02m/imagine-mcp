"""Custom exception hierarchy for imagine-mcp.

All exceptions derive from ImagineError. Messages are actionable and never contain
API key substrings or credentials.
"""

from __future__ import annotations


class ImagineError(Exception):
    """Base exception for imagine-mcp."""


class ValidationError(ImagineError):
    """Input validation failed before any provider call."""


class InvalidActionError(ValidationError):
    """Action is not one of the supported values."""


class InvalidProviderError(ValidationError):
    """Provider is not in {gemini, openai, grok}."""


class InvalidTierError(ValidationError):
    """Tier is not in {poor, rich}."""


class InvalidMediaTypeError(ValidationError):
    """Media type is not in {image, video}."""


class InvalidURLError(ValidationError):
    """URL scheme is not http or https (SSRF/LFI prevention)."""


class ProviderError(ImagineError):
    """Provider-side error (network, quota, auth, or API refusal)."""


class ProviderUnsupportedError(ProviderError):
    """Provider does not support this (action, media, tier) combo."""


class CredentialMissingError(ProviderError):
    """API key for the requested provider is not available."""


class RateLimitError(ProviderError):
    """Provider rate limit exceeded. retry_after in seconds (None if unknown)."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ProviderAPIError(ProviderError):
    """Provider API returned a non-2xx response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class VideoJobTimeoutError(ImagineError):
    """Async video generation exceeded sync-poll timeout. Use job_id to resume."""

    def __init__(self, message: str, job_id: str) -> None:
        super().__init__(message)
        self.job_id = job_id


class MediaDetectError(ImagineError):
    """Could not determine image vs video from URL content-type and extension."""
