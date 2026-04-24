"""Entry point with mode dispatch."""

from __future__ import annotations

import os
import sys


def main() -> None:
    mode = (os.environ.get("MCP_MODE") or "").strip().lower()

    if "--stdio" in sys.argv or os.environ.get("MCP_TRANSPORT") == "stdio":
        from mcp_core.transport import run_smart_stdio_proxy

        daemon_cmd = [sys.executable, "-m", "imagine_mcp"]
        sys.exit(run_smart_stdio_proxy("imagine-mcp", daemon_cmd))

    if mode in ("", "http-local-relay", "local-relay"):
        from imagine_mcp.server import main as http_local_relay_main

        http_local_relay_main()
        return

    raise SystemExit(
        f"Unsupported MCP_MODE={mode!r}. Supported: local-relay (default) "
        "or set MCP_TRANSPORT=stdio / pass --stdio for stdio proxy."
    )


if __name__ == "__main__":
    main()
