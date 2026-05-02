"""Entry point with mode dispatch.

Two independent modes (per spec 2026-05-01-stdio-pure-http-multiuser.md):

- ``stdio`` (default) -- pure local single-user. Reads creds from env vars
  only; exits 1 if all three of ``GEMINI_API_KEY``/``OPENAI_API_KEY``/
  ``XAI_API_KEY`` are missing. Universal MCP client compatibility
  (Claude Code, Cursor, VS Code Copilot, etc.). No daemon, no browser.

- ``http`` (opt-in via ``--http`` flag, ``MCP_TRANSPORT=http`` or
  ``TRANSPORT_MODE=http`` env var) -- HTTP daemon, always multi-user
  remote-style. Set ``PUBLIC_URL`` + ``MCP_DCR_SERVER_SECRET`` to bind
  publicly with per-JWT-sub credential isolation; otherwise serves on
  127.0.0.1:<port> for local self-host.
"""

from __future__ import annotations

import asyncio
import os
import sys

_STDIO_MISSING_CRED_MSG = """\
[imagine-mcp] No provider API keys set. Stdio mode requires at least one of:
  - GEMINI_API_KEY
  - OPENAI_API_KEY
  - XAI_API_KEY

Options:
  1. Set env in plugin config:
     {"command": "uvx", "args": ["imagine-mcp"], "env": {"GEMINI_API_KEY": "..."}}

  2. Switch to HTTP mode (browser-based setup):
     See imagine-mcp/docs/setup-manual.md "Method 5: Self-Hosting HTTP Mode"

Documentation: https://github.com/n24q02m/imagine-mcp#setup
"""


def main() -> None:
    is_http = (
        "--http" in sys.argv
        or os.environ.get("MCP_TRANSPORT") == "http"
        or os.environ.get("TRANSPORT_MODE") == "http"
    )

    if is_http:
        from imagine_mcp.server import run_http

        asyncio.run(run_http())
        return

    # Default: stdio. FastMCP stdio server directly on stdin/stdout.
    # No daemon, no bridge. Env-only creds; exit 1 if all 3 missing
    # (server has no functional tools without at least one provider).
    if not any(
        os.environ.get(k) for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY")
    ):
        sys.stderr.write(_STDIO_MISSING_CRED_MSG)
        raise SystemExit(1)

    from imagine_mcp.server import build_app

    build_app().run(transport="stdio")


if __name__ == "__main__":
    main()
