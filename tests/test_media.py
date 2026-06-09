from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from imagine_mcp.errors import InvalidURLError, MediaDetectError
from imagine_mcp.media import (
    SSRFSafeTransport,
    _extract_extension,
    detect_media_type,
    download_to_path,
    get_ssrf_safe_client,
    resolve_image_mime,
    sniff_image_mime,
    validate_url_and_get_ip,
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


class TestSSRFProtection:
    """Regression tests locking in the SSRF protections in media.py.

    The transport must (1) reject URLs resolving to internal/private/loopback/
    link-local IPs, (2) reject non-http(s) schemes, and (3) DNS-pin by rewriting
    the request URL to the validated IP while setting ``sni_hostname`` to the
    original host so TLS certificate verification still targets the hostname (not
    the IP). These guard against httpx changing the ``sni_hostname`` extension
    semantics (pyproject caps httpx <1.0 for this reason).
    """

    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/x",  # IPv4 loopback
            "http://169.254.169.254/latest/meta-data",  # cloud metadata link-local
            "http://10.0.0.1/",  # RFC1918 private
            "http://192.168.1.1/",  # RFC1918 private
            "http://[::1]/",  # IPv6 loopback
        ],
    )
    def test_rejects_internal_ips(self, url: str) -> None:
        with pytest.raises(InvalidURLError, match="internal/private IP"):
            validate_url_and_get_ip(url, "redirect_url")

    @pytest.mark.parametrize(
        "url", ["file:///etc/passwd", "ftp://host/x", "gopher://h/"]
    )
    def test_rejects_non_http_scheme(self, url: str) -> None:
        with pytest.raises(InvalidURLError, match="scheme"):
            validate_url_and_get_ip(url, "redirect_url")

    def test_rejects_missing_hostname(self) -> None:
        with pytest.raises(InvalidURLError, match="missing hostname"):
            validate_url_and_get_ip("http:///nohost", "redirect_url")

    def test_transport_pins_ip_and_sets_sni(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """handle_request must rewrite host->validated IP and set sni_hostname to
        the original host so TLS verification targets the hostname, not the IP."""
        captured: dict = {}

        def fake_validate(url: str, param: str) -> str:
            return "93.184.216.34"  # pretend example.com resolved here (public)

        def fake_super(
            self: SSRFSafeTransport, request: httpx.Request
        ) -> httpx.Response:
            captured["host"] = request.url.host
            captured["sni"] = request.extensions.get("sni_hostname")
            captured["host_header"] = request.headers.get("Host")
            return httpx.Response(200)

        monkeypatch.setattr("imagine_mcp.media.validate_url_and_get_ip", fake_validate)
        monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fake_super)

        transport = SSRFSafeTransport()
        req = httpx.Request("GET", "https://example.com/img.png")
        transport.handle_request(req)

        assert captured["host"] == "93.184.216.34"  # pinned to validated IP
        assert captured["sni"] == "example.com"  # TLS verifies against hostname
        assert captured["host_header"] == "example.com"  # virtual-host routing intact

    def test_transport_passes_through_non_http_scheme(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-http(s) schemes bypass IP pinning (httpx will reject them itself)."""
        called = {"validated": False}

        def fake_validate(url: str, param: str) -> str:
            called["validated"] = True
            return "1.2.3.4"

        monkeypatch.setattr("imagine_mcp.media.validate_url_and_get_ip", fake_validate)
        monkeypatch.setattr(
            httpx.HTTPTransport,
            "handle_request",
            lambda self, request: httpx.Response(200),
        )
        transport = SSRFSafeTransport()
        transport.handle_request(httpx.Request("GET", "file:///etc/passwd"))
        assert called["validated"] is False


def test_get_ssrf_safe_client_singleton() -> None:
    client1 = get_ssrf_safe_client()
    client2 = get_ssrf_safe_client()
    assert client1 is client2
    assert isinstance(client1, httpx.Client)
    assert isinstance(client1._transport, SSRFSafeTransport)


def test_validate_url_and_get_ip_success(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    # Mock socket.getaddrinfo to return a public IPv4
    # addr_info format: (family, type, proto, canonname, sockaddr)
    # sockaddr for AF_INET is (address, port)
    mock_addr_info = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))
    ]
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: mock_addr_info)

    ip = validate_url_and_get_ip("http://example.com/foo", "param")
    assert ip == "93.184.216.34"


def test_validate_url_and_get_ip_ipv4_mapped_ipv6(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import socket

    # Mock socket.getaddrinfo to return an IPv4-mapped IPv6 address (::ffff:93.184.216.34)
    # sockaddr for AF_INET6 is (address, port, flow info, scope id)
    mock_addr_info = [
        (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::ffff:93.184.216.34", 80, 0, 0))
    ]
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: mock_addr_info)

    ip = validate_url_and_get_ip("http://example.com/foo", "param")
    # It should extract the underlying IPv4 if it's mapped
    assert ip == "::ffff:93.184.216.34"


def test_validate_url_and_get_ip_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    import concurrent.futures

    def mock_result(timeout=None):
        raise concurrent.futures.TimeoutError()

    mock_future = MagicMock()
    mock_future.result.side_effect = mock_result

    monkeypatch.setattr(
        "imagine_mcp.media._DNS_RESOLVER_POOL.submit",
        lambda *args, **kwargs: mock_future,
    )

    with pytest.raises(InvalidURLError, match="DNS resolution timed out"):
        validate_url_and_get_ip("http://example.com/foo", "param")


def test_validate_url_and_get_ip_gaierror(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    def mock_getaddrinfo(*args, **kwargs):
        raise socket.gaierror(-2, "Name or service not known")

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    with pytest.raises(InvalidURLError, match="Could not resolve hostname"):
        validate_url_and_get_ip("http://nonexistent.example.com", "param")


def test_validate_url_and_get_ip_no_ips(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [])

    with pytest.raises(InvalidURLError, match="No valid IP found"):
        validate_url_and_get_ip("http://example.com", "param")


def test_transport_sets_missing_host_header(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_validate(url: str, param: str) -> str:
        return "93.184.216.34"

    def fake_super(self, request: httpx.Request) -> httpx.Response:
        captured["host_header"] = request.headers.get("Host")
        return httpx.Response(200)

    monkeypatch.setattr("imagine_mcp.media.validate_url_and_get_ip", fake_validate)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fake_super)

    transport = SSRFSafeTransport()
    # Create request without Host header
    req = httpx.Request("GET", "https://example.com/img.png")
    if "Host" in req.headers:
        del req.headers["Host"]

    transport.handle_request(req)
    assert captured["host_header"] == "example.com"


def test_detect_media_type_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockClient:
        def head(self, url, **kw):
            raise httpx.HTTPError("HEAD failed")

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: MockClient())
    with pytest.raises(MediaDetectError, match="HEAD request failed"):
        detect_media_type("https://example.com/foo")


def test_detect_media_type_invalid_url_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockClient:
        def head(self, url, **kw):
            raise InvalidURLError("unsafe")

    monkeypatch.setattr("imagine_mcp.media.get_ssrf_safe_client", lambda: MockClient())
    with pytest.raises(
        MediaDetectError, match="HEAD request failed due to invalid redirect"
    ):
        detect_media_type("https://example.com/foo")
