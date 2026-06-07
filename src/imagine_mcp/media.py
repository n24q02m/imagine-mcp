"""Media type detection and download helpers."""

from __future__ import annotations

import concurrent.futures
import ipaddress
import os
import socket
from pathlib import Path
from typing import Any, Literal, cast
from urllib.parse import urlparse

import httpcore
import httpx

from imagine_mcp.errors import InvalidURLError, MediaDetectError

MediaType = Literal["image", "video"]

_DNS_RESOLVER_POOL = concurrent.futures.ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="dns_resolver"
)

_SAFE_URL_SCHEMES = frozenset({"http", "https"})

_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".svg"}
_VIDEO_EXT = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv", ".m4v"}

_IMAGE_MIME_PREFIX = "image/"
_VIDEO_MIME_PREFIX = "video/"

# Most image hosts serve JPEG, so it is the safest fallback when neither the
# Content-Type header nor the magic bytes identify the format.
_IMAGE_FALLBACK_MIME = "image/jpeg"


def sniff_image_mime(data: bytes) -> str | None:
    """Return an ``image/*`` mime type by sniffing magic bytes, or None.

    Recognizes PNG, JPEG, WEBP, GIF, and the HEIC/HEIF ISO-BMFF families.
    """
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"GIF8"):
        return "image/gif"
    # HEIC/HEIF: ISO-BMFF box with an ``ftyp`` brand at offset 4.
    if data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand in (b"heic", b"heix", b"hevc", b"hevx"):
            return "image/heic"
        if brand in (b"heif", b"mif1", b"msf1"):
            return "image/heif"
    return None


def resolve_image_mime(content_type: str | None, data: bytes) -> str:
    """Resolve the mime type for fetched image bytes.

    Precedence: a real ``image/*`` Content-Type header (params stripped,
    lowercased) wins; otherwise magic-byte sniffing; otherwise the JPEG
    fallback (the most common web image format).
    """
    if content_type:
        ctype = content_type.split(";", 1)[0].strip().lower()
        if ctype.startswith(_IMAGE_MIME_PREFIX):
            return ctype
    sniffed = sniff_image_mime(data)
    if sniffed is not None:
        return sniffed
    return _IMAGE_FALLBACK_MIME


class SSRFSafeBackend(httpcore.NetworkBackend):
    """Custom httpcore backend that implements DNS pinning and validation."""

    def __init__(self, backend: httpcore.NetworkBackend):
        self._backend = backend

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Any = None,
    ) -> httpcore.NetworkStream:
        # Resolve and validate the IP address to prevent TOCTOU DNS rebinding.
        # We use "url" as the param name for consistency with dispatcher's fail-fast check.
        ip = _validate_hostname_and_get_ip(host, port, "url")
        return self._backend.connect_tcp(
            ip,
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )

    def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options: Any = None,
    ) -> httpcore.NetworkStream:
        raise InvalidURLError("Unix sockets are not allowed.")


class SSRFSafeTransport(httpx.HTTPTransport):
    """Custom transport that prevents SSRF via DNS pinning in the backend.

    It uses SSRFSafeBackend to ensure that hostname resolution is validated
    against public IP ranges and pinned during the connection phase, while
    preserving the original hostname in the request for TLS/SNI.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        # Inject our security-hardened backend into the connection pool.
        # We use the internal _pool attribute which is standard for httpx.HTTPTransport.
        pool = getattr(self, "_pool", None)
        if pool is not None:
            backend = getattr(pool, "_network_backend", None)
            if isinstance(backend, httpcore.NetworkBackend):
                # Use setattr to satisfy type checkers for internal attribute access.
                setattr(pool, "_network_backend", SSRFSafeBackend(backend))

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        url = request.url
        if url.scheme.lower() not in _SAFE_URL_SCHEMES:
            raise InvalidURLError(
                f"Invalid URL scheme {url.scheme!r}. Only http/https are allowed."
            )

        # We rely on SSRFSafeBackend to perform the DNS pinning and validation
        # during the connection phase. This ensures the TLS handshake uses
        # the original request hostname for SNI and certificate verification.
        return super().handle_request(request)


def _validate_hostname_and_get_ip(hostname: str, port: int | None, param: str) -> str:
    """Core logic to resolve a hostname and validate it is a public IP.

    Returns the first validated IP address string.
    Raises InvalidURLError if the resolution fails or points to an unsafe IP.
    """
    if not hostname:
        raise InvalidURLError(f"Invalid {param}: missing hostname.")

    try:
        # Wrap the blocking getaddrinfo in a thread with a short timeout
        # to prevent DoS attacks via malicious DNS servers.
        future = _DNS_RESOLVER_POOL.submit(
            socket.getaddrinfo, hostname, port, socket.AF_UNSPEC
        )
        # Short timeout to fail fast on tarpit DNS
        addr_info = cast(list[Any], future.result(timeout=2.0))

        for res in addr_info:
            # res[4] is the sockaddr tuple. The first element is the IP string.
            ip_str = str(res[4][0])
            ip_obj = ipaddress.ip_address(ip_str)

            # Extract underlying IPv4 if it's an IPv4-mapped IPv6 address (e.g. ::ffff:127.0.0.1)
            if ip_obj.version == 6 and ip_obj.ipv4_mapped:
                ip_obj = ip_obj.ipv4_mapped

            # Strictly allow only public, non-multicast IPs.
            if not ip_obj.is_global or ip_obj.is_multicast:
                raise InvalidURLError(
                    f"Invalid {param}: URL resolves to an internal/private IP."
                )

            # Return the first safe IP
            return ip_str

        raise InvalidURLError(f"Invalid {param}: No valid IP found for {hostname!r}.")

    except concurrent.futures.TimeoutError as e:
        raise InvalidURLError(
            f"Invalid {param}: DNS resolution timed out for {hostname!r}."
        ) from e
    except socket.gaierror as e:
        raise InvalidURLError(
            f"Invalid {param}: Could not resolve hostname {hostname!r}."
        ) from e


def validate_url_and_get_ip(url: str, param: str) -> str:
    """Verify URL scheme and resolve hostname to a public IP.

    This provides a fail-fast check before initiating a full request.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in _SAFE_URL_SCHEMES:
        raise InvalidURLError(
            f"Invalid {param} scheme {scheme!r}. Only http/https are allowed."
        )

    return _validate_hostname_and_get_ip(parsed.hostname or "", parsed.port, param)


_CLIENT: httpx.Client | None = None


def get_ssrf_safe_client() -> httpx.Client:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = httpx.Client(transport=SSRFSafeTransport())
    return _CLIENT


def detect_media_type(url: str) -> MediaType:
    """Return 'image' or 'video' for a URL.

    Priority: file extension > HEAD request content-type.
    Raises MediaDetectError if neither signals a clear type.
    """
    ext = _extract_extension(url)
    if ext in _IMAGE_EXT:
        return "image"
    if ext in _VIDEO_EXT:
        return "video"

    try:
        client = get_ssrf_safe_client()
        resp = client.head(url, follow_redirects=True, timeout=10)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise MediaDetectError(f"HEAD request failed for {url}: {e}") from e
    except InvalidURLError as e:
        raise MediaDetectError(
            f"HEAD request failed due to invalid redirect for {url}: {e}"
        ) from e

    ctype = resp.headers.get("content-type", "").lower()
    if ctype.startswith(_IMAGE_MIME_PREFIX):
        return "image"
    if ctype.startswith(_VIDEO_MIME_PREFIX):
        return "video"

    raise MediaDetectError(
        f"Ambiguous media for {url}: no known extension and content-type={ctype!r}."
    )


def _extract_extension(url: str) -> str:
    """Return lowercase file extension including dot, or '' if none."""
    path = url.split("?", 1)[0].split("#", 1)[0]
    _, ext = os.path.splitext(path)
    return ext.lower()


def download_to_path(url: str, dest: Path) -> Path:
    """Download URL content to dest path. Returns path."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        client = get_ssrf_safe_client()
        with client.stream("GET", url, follow_redirects=True, timeout=60) as resp:
            resp.raise_for_status()
            with dest.open("wb") as f:
                for chunk in resp.iter_bytes(chunk_size=65536):
                    f.write(chunk)
    except InvalidURLError as e:
        raise httpx.HTTPError(f"Download failed due to invalid redirect: {e}") from e
    return dest
