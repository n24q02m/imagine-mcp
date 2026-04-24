"""Entry point with mode dispatch."""

from __future__ import annotations

import os
import sys


def main() -> None:
    from imagine_mcp.server import main as http_local_relay_main
    from imagine_mcp.server import main_stdio

    mode = os.environ.get("MCP_MODE", "http-local-relay")
    if "--stdio" in sys.argv:
        mode = "stdio-proxy"

    if mode == "stdio-proxy":
        main_stdio()
    elif mode == "http-local-relay":
        http_local_relay_main()
    else:
        raise ValueError(f"Unsupported MCP_MODE={mode!r}")


if __name__ == "__main__":
    main()
