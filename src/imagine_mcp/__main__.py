"""Entry point with mode dispatch.

Modes (parity with wet-mcp / mnemo-mcp / better-code-review-graph):

- ``http local relay`` (default) -- ``run_http``: local HTTP daemon with
  credential form at ``127.0.0.1:<port>/authorize``.
- ``http remote relay (self-host)`` -- ``run_remote_relay``: pull creds from a
  user-deployed relay URL (``MCP_RELAY_URL``) then serve MCP protocol locally.
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
        from imagine_mcp.server import run_remote_relay

        asyncio.run(run_remote_relay())
        return

    if mode in ("", "local-relay", "http-local-relay"):
        from imagine_mcp.server import run_http

        asyncio.run(run_http())
        return

    raise SystemExit(
        f"Unsupported MCP_MODE={mode!r}. Supported: local-relay (default), "
        "remote-relay (requires MCP_RELAY_URL), or set MCP_TRANSPORT=stdio / "
        "pass --stdio for stdio proxy."
    )


if __name__ == "__main__":
    main()
