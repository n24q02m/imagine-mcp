"""imagine-mcp: MCP server for image/video understanding and generation."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("imagine-mcp")
except PackageNotFoundError:
    __version__ = "1.9.0-beta.4"
