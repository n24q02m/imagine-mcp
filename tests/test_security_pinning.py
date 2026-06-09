from __future__ import annotations

import socket
import typing

import httpcore
import httpx
import pytest

from imagine_mcp.errors import InvalidURLError
from imagine_mcp.media import (
    SSRFSafeBackend,
    SSRFSafeTransport,
    validate_url_and_get_ip,
)


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


def test_ssrf_safe_transport_pinning(monkeypatch):
    # This test verifies that handle_request does NOT rewrite the URL,
    # but the backend DOES use the pinned IP.
    captured_host = []

    def mock_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    # Mock the internal httpcore.SyncBackend.connect_tcp to capture the host used for connection.

    def mock_connect_tcp(self, host, port, **kwargs):
        captured_host.append(host)
        # Return a mock stream to avoid real network call
        return typing.cast(httpcore.NetworkStream, typing.Any)

    monkeypatch.setattr(httpcore.SyncBackend, "connect_tcp", mock_connect_tcp)

    # Mock handle_request to avoid issues with the cast mock stream
    monkeypatch.setattr(
        httpx.HTTPTransport,
        "handle_request",
        lambda self, req: httpx.Response(200, content=b"ok", request=req),
    )

    transport = SSRFSafeTransport()
    request = httpx.Request("GET", "https://example.com/foo")

    # Manually trigger the backend to verify pinning
    backend = transport._pool._network_backend
    backend.connect_tcp("example.com", 443)

    assert captured_host[0] == "93.184.215.14"

    # Now verify handle_request behavior
    transport.handle_request(request)

    # Verification: URL is NOT rewritten anymore
    assert str(request.url) == "https://example.com/foo"
    assert request.headers["Host"] == "example.com"
    assert request.extensions["sni_hostname"] == "example.com"


def test_ssrf_safe_backend_blocks_private(monkeypatch):
    def mock_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.1", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    backend = SSRFSafeBackend()
    with pytest.raises(InvalidURLError, match="internal/private IP"):
        backend.connect_tcp("internal.service", 80)


def test_ssrf_safe_backend_blocks_unix_sockets():
    backend = SSRFSafeBackend()
    with pytest.raises(InvalidURLError, match="Unix sockets are not allowed"):
        backend.connect_unix_socket("/var/run/docker.sock")
