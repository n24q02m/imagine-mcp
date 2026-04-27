"""Entry point with mode dispatch.

Modes (parity with wet-mcp / mnemo-mcp / better-code-review-graph):

- ``http local relay`` (default) -- ``run_http``: local HTTP daemon with
  credential form at ``127.0.0.1:<port>/authorize``.
- ``http remote relay (multi-user)`` -- same ``run_http`` codepath, activated
  by setting ``PUBLIC_URL`` (and ``MCP_DCR_SERVER_SECRET``). Daemon binds
  ``0.0.0.0:8080`` and scopes LLM API keys per JWT ``sub``.
- ``stdio proxy`` -- ``run_smart_stdio_proxy``: bridge stdin/stdout to a local
  HTTP daemon (same backend as http local relay, client-side transport only).
"""

from __future__ import annotations

import asyncio
import os
import sys


def main() -> None:
    mode = (os.environ.get("MCP_MODE") or "").strip().lower()

    if "--stdio" in sys.argv or os.environ.get("MCP_TRANSPORT") == "stdio":
        from mcp_core.transport import run_smart_stdio_proxy

        daemon_cmd = [sys.executable, "-m", "imagine_mcp"]
        sys.exit(run_smart_stdio_proxy("imagine-mcp", daemon_cmd))

    if mode == "remote-relay":
        raise SystemExit(
            "MCP_MODE=remote-relay is deprecated. The unified http daemon "
            "(`run_http`) now handles both single-user (default) and "
            "multi-user remote modes; set PUBLIC_URL + MCP_DCR_SERVER_SECRET "
            "to enable multi-user remote mode."
        )

    if mode in ("", "local-relay", "http-local-relay"):
        from imagine_mcp.server import run_http

        asyncio.run(run_http())
        return

    raise SystemExit(
        f"Unsupported MCP_MODE={mode!r}. Supported: local-relay (default; set "
        "PUBLIC_URL + MCP_DCR_SERVER_SECRET for multi-user remote mode), or set "
        "MCP_TRANSPORT=stdio / pass --stdio for stdio proxy."
    )


if __name__ == "__main__":
    main()
