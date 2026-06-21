"""Media type detection and download helpers."""

from __future__ import annotations

import asyncio
import concurrent.futures
import ipaddress
import os
import socket
import threading
import typing
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import anyio
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
    """Custom network backend that implements DNS pinning to prevent TOCTOU SSRF.

    It resolves the hostname, validates the IP against local/private ranges,
    and then pins the TCP connection to that IP while preserving the original
    hostname for TLS certificate validation.
    """

    def __init__(self) -> None:
        self._backend = httpcore.SyncBackend()

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: typing.Iterable[httpcore.SOCKET_OPTION] | None = None,
    ) -> httpcore.NetworkStream:
        # Pin the request to a validated IP to prevent TOCTOU DNS rebinding.
        ip = _validate_hostname_and_get_ip(host, port, "url")
        return self._backend.connect_tcp(
            host=ip,
            port=port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )

    def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options: typing.Iterable[httpcore.SOCKET_OPTION] | None = None,
    ) -> httpcore.NetworkStream:
        # Explicitly block Unix sockets for enhanced SSRF security.
        raise InvalidURLError("Unix sockets are not allowed.")

    def sleep(self, seconds: float) -> None:
        return self._backend.sleep(seconds)


class AsyncSSRFSafeBackend(httpcore.AsyncNetworkBackend):
    """Async version of SSRFSafeBackend."""

    def __init__(self) -> None:
        self._backend = httpcore.AnyIOBackend()

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: typing.Iterable[httpcore.SOCKET_OPTION] | None = None,
    ) -> httpcore.AsyncNetworkStream:
        # Blocking DNS resolution offloaded to thread.
        ip = await asyncio.to_thread(_validate_hostname_and_get_ip, host, port, "url")
        return await self._backend.connect_tcp(
            host=ip,
            port=port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )

    async def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options: typing.Iterable[httpcore.SOCKET_OPTION] | None = None,
    ) -> httpcore.AsyncNetworkStream:
        raise InvalidURLError("Unix sockets are not allowed.")

    async def sleep(self, seconds: float) -> None:
        return await self._backend.sleep(seconds)


class SSRFSafeTransport(httpx.HTTPTransport):
    """Custom transport that uses SSRFSafeBackend for DNS pinning."""

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)
        # Inject the custom backend into the internal connection pool.
        # This is safe because HTTPTransport.__init__ creates the pool.
        self._pool._network_backend = SSRFSafeBackend()  # type: ignore

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        url = request.url
        if url.scheme.lower() not in _SAFE_URL_SCHEMES:
            return super().handle_request(request)

        # Ensure Host header is set for virtual hosting.
        if "Host" not in request.headers:
            request.headers["Host"] = url.host

        # Set SNI extension for TLS.
        request.extensions["sni_hostname"] = url.host

        return super().handle_request(request)


class AsyncSSRFSafeTransport(httpx.AsyncHTTPTransport):
    """Async version of SSRFSafeTransport."""

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)
        self._pool._network_backend = AsyncSSRFSafeBackend()  # type: ignore

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        url = request.url
        if url.scheme.lower() not in _SAFE_URL_SCHEMES:
            return await super().handle_async_request(request)

        if "Host" not in request.headers:
            request.headers["Host"] = url.host

        request.extensions["sni_hostname"] = url.host

        return await super().handle_async_request(request)


def _validate_hostname_and_get_ip(hostname: str, port: int | None, param: str) -> str:
    """Resolve hostname to a public IP and validate it.

    Returns the first validated IP address string.
    Raises InvalidURLError if resolution fails or returns an unsafe IP.
    """
    try:
        # Wrap the blocking getaddrinfo in a thread with a short timeout
        # to prevent DoS attacks via malicious DNS servers.
        future = _DNS_RESOLVER_POOL.submit(
            socket.getaddrinfo, hostname, port, socket.AF_UNSPEC
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

    return _validate_hostname_and_get_ip(hostname, parsed.port, param)


class _ClientManager:
    def __init__(self) -> None:
        self._client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None
        self._lock = threading.Lock()

    def get_client(self) -> httpx.Client:
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._client = httpx.Client(transport=SSRFSafeTransport())
        return self._client

    def get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            with self._lock:
                if self._async_client is None:
                    self._async_client = httpx.AsyncClient(
                        transport=AsyncSSRFSafeTransport()
                    )
        return self._async_client

    def reset(self) -> None:
        with self._lock:
            self._client = None
            self._async_client = None


_MANAGER = _ClientManager()


def get_ssrf_safe_client() -> httpx.Client:
    return _MANAGER.get_client()


def get_ssrf_safe_async_client() -> httpx.AsyncClient:
    return _MANAGER.get_async_client()


def _reset_ssrf_safe_client() -> None:
    _MANAGER.reset()


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


async def detect_media_type_async(url: str) -> MediaType:
    """Async version of detect_media_type."""
    ext = _extract_extension(url)
    if ext in _IMAGE_EXT:
        return "image"
    if ext in _VIDEO_EXT:
        return "video"

    try:
        client = get_ssrf_safe_async_client()
        resp = await client.head(url, follow_redirects=True, timeout=10)
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


def _write_response(resp: httpx.Response, dest: Path) -> None:
    max_size = 50 * 1024 * 1024  # 50MB limit to prevent DoS
    bytes_read = 0
    with dest.open("wb") as f:
        for chunk in resp.iter_bytes(chunk_size=65536):
            bytes_read += len(chunk)
            if bytes_read > max_size:
                raise httpx.HTTPError(
                    f"Download failed: Exceeded maximum size of {max_size} bytes"
                )
            f.write(chunk)


async def _write_response_async(resp: httpx.Response, dest: Path) -> None:
    max_size = 50 * 1024 * 1024  # 50MB limit to prevent DoS
    bytes_read = 0
    # ⚡ Bolt: Replace high-overhead asyncio.to_thread with anyio.open_file
    # Expected impact: Dramatically reduces context-switching overhead on file chunk writes
    async with await anyio.open_file(dest, "wb") as f:
        async for chunk in resp.aiter_bytes(chunk_size=65536):
            bytes_read += len(chunk)
            if bytes_read > max_size:
                raise httpx.HTTPError(
                    f"Download failed: Exceeded maximum size of {max_size} bytes"
                )
            await f.write(chunk)


def download_to_path(url: str, dest: Path) -> Path:
    """Download URL content to dest path. Returns path."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        client = get_ssrf_safe_client()
        with client.stream("GET", url, follow_redirects=True, timeout=60) as resp:
            resp.raise_for_status()
            _write_response(resp, dest)
    except InvalidURLError as e:
        raise httpx.HTTPError(f"Download failed due to invalid redirect: {e}") from e
    except Exception:
        if dest.exists():
            dest.unlink(missing_ok=True)
        raise
    return dest


async def download_to_path_async(url: str, dest: Path) -> Path:
    """Async version of download_to_path."""
    await asyncio.to_thread(dest.parent.mkdir, parents=True, exist_ok=True)
    try:
        client = get_ssrf_safe_async_client()
        async with client.stream("GET", url, follow_redirects=True, timeout=60) as resp:
            resp.raise_for_status()
            await _write_response_async(resp, dest)
    except InvalidURLError as e:
        raise httpx.HTTPError(f"Download failed due to invalid redirect: {e}") from e
    except Exception:
        if await asyncio.to_thread(dest.exists):
            await asyncio.to_thread(dest.unlink, missing_ok=True)
        raise
    return dest


async def emit_media(
    data: bytes, suffix: str, key: str, output_mode: str
) -> dict[str, str]:
    """Build the media-output fields for a generated asset, honouring output_mode.

    ``output_mode``:
      - ``"base64"``: return ``{<key>_base64: ...}`` only -- NO disk write
        (required on the ephemeral Cloudflare container FS).
      - ``"path"``:   write ``<cache>/generations/<uuid><suffix>`` and return
        ``{<key>_path: ...}`` only.
      - ``"both"``:   write the file AND return both fields (default).

    ``key`` is ``"image"`` or ``"video"``; ``suffix`` includes the dot
    (``".png"`` / ``".mp4"``).
    """
    import base64 as _b64
    import uuid as _uuid

    import platformdirs as _pd

    out: dict[str, str] = {}
    if output_mode in ("base64", "both"):
        out[f"{key}_base64"] = _b64.b64encode(data).decode()
    if output_mode in ("path", "both"):
        out_dir = Path(_pd.user_cache_dir("imagine-mcp")) / "generations"
        await asyncio.to_thread(out_dir.mkdir, parents=True, exist_ok=True)
        out_path = out_dir / f"{_uuid.uuid4().hex}{suffix}"
        await asyncio.to_thread(out_path.write_bytes, data)
        out[f"{key}_path"] = str(out_path)
    return out
