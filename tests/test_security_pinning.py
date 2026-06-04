from __future__ import annotations

import socket

import httpx
import pytest

from imagine_mcp.errors import InvalidURLError
from imagine_mcp.media import SSRFSafeTransport, validate_url_and_get_ip


def test_validate_url_and_get_ip_success(monkeypatch):
    def mock_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    ip = validate_url_and_get_ip("http://example.com/", "test")
    assert ip == "93.184.215.14"


def test_validate_url_and_get_ip_private(monkeypatch):
    def mock_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    with pytest.raises(InvalidURLError, match="internal/private IP"):
        validate_url_and_get_ip("http://example.com/", "test")


def test_ssrf_safe_transport_no_rewriting(monkeypatch):
    # This test verifies that handle_request NO LONGER rewrites the URL.
    transport = SSRFSafeTransport()

    # Patch super().handle_request to return the request for verification
    monkeypatch.setattr(
        httpx.HTTPTransport,
        "handle_request",
        lambda self, req: httpx.Response(200, content=b"ok", request=req),
    )

    request = httpx.Request("GET", "https://example.com/foo")
    transport.handle_request(request)

    # Verification: URL is unchanged
    assert str(request.url) == "https://example.com/foo"


def test_ssrf_safe_network_backend_pinning(monkeypatch):
    # This test verifies that the backend resolves and connects to the IP.
    def mock_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    import httpcore

    from imagine_mcp.media import SSRFSafeNetworkBackend

    # Mock the underlying sync backend
    class MockBackend(httpcore.NetworkBackend):
        def connect_tcp(
            self, host, port, timeout=None, local_address=None, socket_options=None
        ):
            # Verify that we are connecting to the IP, not the hostname
            assert host == "93.184.215.14"
            return "mock_stream"

        def connect_unix_socket(self, path, timeout=None, socket_options=None):
            return "mock_stream"

    safe_backend = SSRFSafeNetworkBackend(backend=MockBackend())
    stream = safe_backend.connect_tcp("example.com", 80)
    assert stream == "mock_stream"


def test_ssrf_safe_transport_blocks_private(monkeypatch):
    # This test verifies that even if the transport doesn't rewrite the URL,
    # the underlying backend will still block private IPs.
    # Since we can't easily mock the connection phase here without real httpcore calls,
    # we just verify that validate_url_and_get_ip still works as expected.
    def mock_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.1", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)


    # In our new implementation, handle_request itself doesn't call validate_url_and_get_ip.
    # It's called when the connection is made.
    # So we test the backend directly for this.

    from imagine_mcp.media import SSRFSafeNetworkBackend

    safe_backend = SSRFSafeNetworkBackend()
    with pytest.raises(InvalidURLError, match="internal/private IP"):
        safe_backend.connect_tcp("internal.service", 80)


def test_ssrf_safe_transport_blocks_non_safe_schemes():
    transport = SSRFSafeTransport()
    request = httpx.Request("GET", "ftp://example.com/foo")
    with pytest.raises(InvalidURLError, match="Invalid URL scheme"):
        transport.handle_request(request)
