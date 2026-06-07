from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from imagine_mcp.errors import InvalidURLError, MediaDetectError
from imagine_mcp.media import (
    _extract_extension,
    detect_media_type,
    download_to_path,
    resolve_image_mime,
    sniff_image_mime,
)

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 16
_WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 16
_GIF = b"GIF89a" + b"\x00" * 16
_HEIC = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00" + b"\x00" * 8
_HEIF = b"\x00\x00\x00\x18ftypmif1\x00\x00\x00\x00" + b"\x00" * 8


def test_sniff_image_mime_magic_bytes() -> None:
    assert sniff_image_mime(_PNG) == "image/png"
    assert sniff_image_mime(_JPEG) == "image/jpeg"
    assert sniff_image_mime(_WEBP) == "image/webp"
    assert sniff_image_mime(_GIF) == "image/gif"
    assert sniff_image_mime(_HEIC) == "image/heic"
    assert sniff_image_mime(_HEIF) == "image/heif"
    assert sniff_image_mime(b"not-an-image") is None


def test_resolve_image_mime_content_type_precedence() -> None:
    # Real image/* Content-Type wins even when bytes say PNG.
    assert resolve_image_mime("image/jpeg", _PNG) == "image/jpeg"
    # Params stripped and lowercased.
    assert resolve_image_mime("Image/WEBP; charset=binary", _PNG) == "image/webp"


def test_resolve_image_mime_sniff_when_header_unhelpful() -> None:
    # Non-image Content-Type falls through to magic-byte sniffing.
    assert resolve_image_mime("application/octet-stream", _JPEG) == "image/jpeg"
    assert resolve_image_mime(None, _GIF) == "image/gif"
    assert resolve_image_mime("", _WEBP) == "image/webp"


def test_resolve_image_mime_unknown_falls_back_to_jpeg() -> None:
    assert resolve_image_mime(None, b"garbage-bytes") == "image/jpeg"
    assert resolve_image_mime("text/html", b"\x00\x01\x02\x03") == "image/jpeg"


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


def test_extract_extension() -> None:
    assert _extract_extension("https://example.com/foo.PNG") == ".png"
    assert _extract_extension("https://example.com/foo.mp4?q=1") == ".mp4"
    assert _extract_extension("https://example.com/foo") == ""


def test_download_to_path_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dest = tmp_path / "subdir" / "test.png"
    content = b"fake-image-bytes"

    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_bytes = MagicMock(return_value=[content])

    class MockClient:
        def stream(self, method, url, **kw):
            return mock_response

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: MockClient())

    result = download_to_path("https://example.com/test.png", dest)

    assert result == dest
    assert dest.exists()
    assert dest.read_bytes() == content
    mock_response.raise_for_status.assert_called_once()


def test_download_to_path_invalid_url(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dest = tmp_path / "test.png"

    class MockClient:
        def stream(self, method, url, **kw):
            raise InvalidURLError("unsafe")

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: MockClient())

    with pytest.raises(
        httpx.HTTPError, match="Download failed due to invalid redirect: unsafe"
    ):
        download_to_path("http://127.0.0.1/test.png", dest)


def test_download_to_path_http_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dest = tmp_path / "test.png"

    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=MagicMock(), response=MagicMock()
    )

    class MockClient:
        def stream(self, method, url, **kw):
            return mock_response

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: MockClient())

    with pytest.raises(httpx.HTTPStatusError, match="404 Not Found"):
        download_to_path("https://example.com/404.png", dest)
