"""Media type detection and download helpers."""

from __future__ import annotations

import concurrent.futures
import ipaddress
import os
import socket
import uuid
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import httpx
import platformdirs

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


class SSRFSafeTransport(httpx.HTTPTransport):
    """Custom transport that implements DNS pinning to prevent TOCTOU SSRF.

    It resolves the hostname, validates the IP against local/private ranges,
    and then rewrites the request URL to use the IP address directly.
    """

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        url = request.url
        if url.scheme.lower() not in _SAFE_URL_SCHEMES:
            return super().handle_request(request)

        host = url.host
        ip = validate_url_and_get_ip(str(url), "redirect_url")

        # Pin the request to the validated IP to prevent TOCTOU DNS rebinding.
        request.url = request.url.copy_with(host=ip)

        # Ensure Host header is set for virtual hosting.
        if "Host" not in request.headers:
            request.headers["Host"] = host

        # Set SNI extension for TLS.
        request.extensions["sni_hostname"] = host

        return super().handle_request(request)


def validate_url_and_get_ip(url: str, param: str) -> str:
    """Verify URL scheme and resolve hostname to a public IP.

    Returns the first validated IP address string.
    Raises InvalidURLError if the URL is unsafe.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in _SAFE_URL_SCHEMES:
        raise InvalidURLError(
            f"Invalid {param} scheme {scheme!r}. Only http/https are allowed."
        )

    hostname = parsed.hostname
    if not hostname:
        raise InvalidURLError(f"Invalid {param}: missing hostname.")

    try:
        # Wrap the blocking getaddrinfo in a thread with a short timeout
        # to prevent DoS attacks via malicious DNS servers.
        # Note: parsed.port may be None, which is fine for getaddrinfo.
        future = _DNS_RESOLVER_POOL.submit(
            socket.getaddrinfo, hostname, parsed.port, socket.AF_UNSPEC
        )
        # Short timeout to fail fast on tarpit DNS
        addr_info = future.result(timeout=2.0)

        for res in addr_info:
            # res[4] is the sockaddr tuple. The first element is the IP string.
            # Explicitly stringify to satisfy type checkers.
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


def get_temp_media_path(extension: str, sub_dir: str = "generations") -> Path:
    """Generate a unique path for temporary media storage.

    Ensures the directory exists.
    """
    out_dir = Path(platformdirs.user_cache_dir("imagine-mcp")) / sub_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{uuid.uuid4().hex}.{extension.lstrip('.')}"


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
