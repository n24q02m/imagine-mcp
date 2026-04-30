"""Media type detection and download helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import httpx

from imagine_mcp.errors import InvalidURLError, MediaDetectError

MediaType = Literal["image", "video"]

_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".svg"}
_VIDEO_EXT = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv", ".m4v"}

_IMAGE_MIME_PREFIX = "image/"
_VIDEO_MIME_PREFIX = "video/"


class SSRFSafeTransport(httpx.HTTPTransport):
    """Custom transport that validates redirect locations against SSRF checks."""

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        from imagine_mcp.dispatcher import _validate_url

        _validate_url(str(request.url), "redirect_url")
        return super().handle_request(request)


# ⚡ Bolt: Global client instance to reuse connection pools across SSRF-safe HTTP requests.
# Creating a new httpx.Client per request adds significant overhead for TCP/TLS handshakes.
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
