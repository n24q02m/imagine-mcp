from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from imagine_mcp.errors import InvalidURLError, MediaDetectError
from imagine_mcp.media import _extract_extension, detect_media_type


def test_detect_by_extension_image() -> None:
    assert detect_media_type("https://example.com/foo.png") == "image"
    assert detect_media_type("https://example.com/bar.jpg?w=100") == "image"
    assert detect_media_type("https://example.com/x.webp#anchor") == "image"


def test_detect_by_extension_video() -> None:
    assert detect_media_type("https://example.com/clip.mp4") == "video"
    assert detect_media_type("https://example.com/video.webm") == "video"


def test_detect_by_content_type_image(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "image/jpeg"}
    mock_response.raise_for_status = MagicMock()

    class MockClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def head(self, url, **kw):
            return mock_response

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: MockClient())
    assert detect_media_type("https://example.com/xyz") == "image"


def test_detect_by_content_type_video(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "video/mp4"}
    mock_response.raise_for_status = MagicMock()

    class MockClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def head(self, url, **kw):
            return mock_response

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: MockClient())
    assert detect_media_type("https://example.com/xyz") == "video"


def test_detect_ambiguous_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "application/octet-stream"}
    mock_response.raise_for_status = MagicMock()

    class MockClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def head(self, url, **kw):
            return mock_response

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: MockClient())
    with pytest.raises(MediaDetectError):
        detect_media_type("https://example.com/unknown-bin")


def test_detect_media_type_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockClient:
        def head(self, url, **kw):
            raise httpx.HTTPError("Mocked HTTP Error")

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: MockClient())
    with pytest.raises(MediaDetectError, match="HEAD request failed for"):
        detect_media_type("https://example.com/no-extension")


def test_detect_media_type_invalid_url_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockClient:
        def head(self, url, **kw):
            raise InvalidURLError("Mocked Invalid URL Error")

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: MockClient())
    with pytest.raises(
        MediaDetectError, match="HEAD request failed due to invalid redirect"
    ):
        detect_media_type("https://example.com/no-extension")


def test_extract_extension() -> None:
    assert _extract_extension("https://example.com/foo.PNG") == ".png"
    assert _extract_extension("https://example.com/foo.mp4?q=1") == ".mp4"
    assert _extract_extension("https://example.com/foo") == ""
