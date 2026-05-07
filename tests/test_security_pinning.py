from __future__ import annotations
import pytest
import httpx
import socket
from imagine_mcp.media import SSRFSafeTransport, validate_url_and_get_ip
from imagine_mcp.errors import InvalidURLError


def test_validate_url_and_get_ip_success(monkeypatch):
    def mock_getaddrinfo(host, port, family):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    ip = validate_url_and_get_ip("http://example.com/", "test")
    assert ip == "93.184.215.14"


def test_validate_url_and_get_ip_private(monkeypatch):
    def mock_getaddrinfo(host, port, family):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    with pytest.raises(InvalidURLError, match="internal/private IP"):
        validate_url_and_get_ip("http://example.com/", "test")


def test_ssrf_safe_transport_pinning(monkeypatch):
    # This test verifies that handle_request rewrites the URL and sets headers.
    def mock_getaddrinfo(host, port, family):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    # Mocking the actual network call so we don't need real internet
    class MockTransport(httpx.HTTPTransport):
        def handle_request(self, request):
            return httpx.Response(200, content=b"ok", request=request)

    transport = SSRFSafeTransport()
    # We need to reach super().handle_request, so we patch HTTPTransport.handle_request
    monkeypatch.setattr(
        httpx.HTTPTransport,
        "handle_request",
        lambda self, req: httpx.Response(200, content=b"ok", request=req),
    )

    request = httpx.Request("GET", "https://example.com/foo")
    transport.handle_request(request)

    # Verification
    assert str(request.url) == "https://93.184.215.14/foo"
    assert request.headers["Host"] == "example.com"
    assert request.extensions["sni_hostname"] == "example.com"


def test_ssrf_safe_transport_blocks_private(monkeypatch):
    def mock_getaddrinfo(host, port, family):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.1", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    transport = SSRFSafeTransport()
    request = httpx.Request("GET", "http://internal.service/foo")

    with pytest.raises(InvalidURLError, match="internal/private IP"):
        transport.handle_request(request)
