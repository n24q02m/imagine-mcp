from __future__ import annotations

import pytest

from imagine_mcp.errors import (
    CredentialMissingError,
    ImagineError,
    InvalidActionError,
    InvalidMediaTypeError,
    InvalidProviderError,
    InvalidTierError,
    MediaDetectError,
    ProviderAPIError,
    ProviderError,
    ProviderUnsupportedError,
    RateLimitError,
    ValidationError,
    VideoJobTimeoutError,
)


def test_hierarchy_validation() -> None:
    assert issubclass(InvalidActionError, ValidationError)
    assert issubclass(InvalidProviderError, ValidationError)
    assert issubclass(InvalidTierError, ValidationError)
    assert issubclass(InvalidMediaTypeError, ValidationError)
    assert issubclass(ValidationError, ImagineError)


def test_hierarchy_provider() -> None:
    assert issubclass(ProviderUnsupportedError, ProviderError)
    assert issubclass(CredentialMissingError, ProviderError)
    assert issubclass(RateLimitError, ProviderError)
    assert issubclass(ProviderAPIError, ProviderError)
    assert issubclass(ProviderError, ImagineError)


def test_hierarchy_misc() -> None:
    assert issubclass(VideoJobTimeoutError, ImagineError)
    assert issubclass(MediaDetectError, ImagineError)


def test_rate_limit_carries_retry_after() -> None:
    err = RateLimitError("rate limit", retry_after=60)
    assert err.retry_after == 60


def test_rate_limit_default_retry_after_none() -> None:
    err = RateLimitError("rate limit")
    assert err.retry_after is None


def test_provider_api_error_carries_status_code() -> None:
    err = ProviderAPIError("bad gateway", status_code=502)
    assert err.status_code == 502


def test_video_job_timeout_carries_job_id() -> None:
    err = VideoJobTimeoutError("timeout", job_id="abc-123")
    assert err.job_id == "abc-123"


def test_all_are_catchable_as_imagine_error() -> None:
    exceptions = [
        InvalidActionError("x"),
        InvalidProviderError("x"),
        InvalidTierError("x"),
        InvalidMediaTypeError("x"),
        ProviderUnsupportedError("x"),
        CredentialMissingError("x"),
        RateLimitError("x"),
        ProviderAPIError("x"),
        VideoJobTimeoutError("x", job_id="y"),
        MediaDetectError("x"),
    ]
    for exc in exceptions:
        with pytest.raises(ImagineError):
            raise exc
