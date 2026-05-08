from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from imagine_mcp.errors import InvalidURLError, MediaDetectError
from imagine_mcp.media import _extract_extension, detect_media_type, download_to_path


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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "sub" / "file.txt"
    url = "https://example.com/file.txt"
    content = [b"chunk1", b"chunk2"]

    mock_response = MagicMock()
    mock_response.iter_bytes.return_value = iter(content)
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.stream.return_value.__enter__.return_value = mock_response

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: mock_client)

    result = download_to_path(url, dest)

    assert result == dest
    assert dest.read_bytes() == b"".join(content)
    assert dest.parent.exists()


def test_download_to_path_invalid_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "file.txt"
    url = "https://example.com/file.txt"

    mock_client = MagicMock()
    mock_client.stream.side_effect = InvalidURLError("Invalid URL")

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: mock_client)

    with pytest.raises(
        httpx.HTTPError, match="Download failed due to invalid redirect: Invalid URL"
    ):
        download_to_path(url, dest)


def test_download_to_path_http_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "file.txt"
    url = "https://example.com/file.txt"

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=MagicMock(), response=MagicMock()
    )

    mock_client = MagicMock()
    mock_client.stream.return_value.__enter__.return_value = mock_response

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: mock_client)

    with pytest.raises(httpx.HTTPStatusError, match="404 Not Found"):
        download_to_path(url, dest)
