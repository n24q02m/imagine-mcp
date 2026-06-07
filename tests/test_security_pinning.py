from __future__ import annotations

import socket
from unittest.mock import MagicMock

import httpcore
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


def test_ssrf_safe_transport_pinning(monkeypatch):
    # This test verifies that SSRFSafeBackend pins the TCP connection to the IP
    # while preserving the hostname for TLS.

    # 1. Mock DNS resolution
    def mock_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 443))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    # 2. Mock the underlying network backend to record calls
    mock_backend = MagicMock(spec=httpcore.NetworkBackend)
    mock_stream = MagicMock(spec=httpcore.NetworkStream)
    mock_backend.connect_tcp.return_value = mock_stream
    # start_tls must return the stream (or a new one)
    mock_stream.start_tls.return_value = mock_stream
    # Mock read for the HTTP response
    mock_stream.read.return_value = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"

    # 3. Create transport and inject mock backend
    transport = SSRFSafeTransport()
    # Replace the actual backend with our mock
    transport._pool._network_backend._backend = mock_backend

    # 4. Perform request
    with httpx.Client(transport=transport) as client:
        resp = client.get("https://example.com/foo")

    # 5. Verification
    assert resp.status_code == 200
    assert resp.text == "ok"

    # Check TCP connection was to the IP
    args, kwargs = mock_backend.connect_tcp.call_args
    assert args[0] == "93.184.215.14"
    assert args[1] == 443

    # Check TLS handshake used the HOSTNAME
    # httpcore calls start_tls(ssl_context, server_hostname=...)
    args, kwargs = mock_stream.start_tls.call_args
    assert kwargs["server_hostname"] == "example.com"

    # Verify request URL was NOT rewritten (it's handled at connection level now)
    assert str(resp.request.url) == "https://example.com/foo"


def test_ssrf_safe_transport_blocks_private(monkeypatch):
    def mock_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.1", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    transport = SSRFSafeTransport()

    # SSRFSafeBackend will raise InvalidURLError during connect_tcp
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(InvalidURLError, match="internal/private IP"),
    ):
        client.get("http://internal.service/foo")
