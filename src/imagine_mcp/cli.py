"""Console-script entry: mounts the shared mcp_core CLI builder.

Bare invocation and any leading-dash argv (e.g. --http) start the server via
``_serve`` exactly as ``__main__.main()`` used to before this module existed;
a leading positional argv[0] routes to a subcommand (``config``/``relay``/
``doctor``) instead. ``--version``/``-h``/``--help`` are intercepted here,
before ``build_cli`` ever sees them: ``build_cli`` treats every leading-dash
argv as an opaque server flag and passes it straight through to ``serve``
(see ``mcp_core/cli.py`` module docstring) -- without this interception
``imagine-mcp --version`` would start the stdio server and hang on stdin
instead of printing a version and exiting.
"""

from __future__ import annotations

import asyncio
import os
import sys

from mcp_core import build_cli

from imagine_mcp.relay_setup import PLUGIN_NAME

_STDIO_MISSING_CRED_MSG = """\
[imagine-mcp] No provider API keys set. Stdio mode requires at least one of:
  - GEMINI_API_KEY
  - OPENAI_API_KEY
  - XAI_API_KEY

Options:
  1. Set env in plugin config:
     {"command": "uvx", "args": ["imagine-mcp"], "env": {"GEMINI_API_KEY": "..."}}

  2. Switch to HTTP mode (browser-based setup):
     See https://mcp.n24q02m.com/servers/imagine-mcp/setup/ "Self-Hosting HTTP Mode"

Documentation: https://mcp.n24q02m.com/servers/imagine-mcp/setup/
"""

_HELP_TEXT = """\
imagine-mcp -- image/video understanding & generation (Gemini/OpenAI/Grok)

Usage:
  imagine-mcp                  Start the server (stdio, default)
  imagine-mcp --http           Start the server (HTTP daemon)
  imagine-mcp doctor           Environment + config health check
  imagine-mcp config status    Show credential configuration state
  imagine-mcp config delete    Delete stored credentials (--yes to skip the prompt)
  imagine-mcp relay status     Show the active relay session, if any
  imagine-mcp relay open       Reopen the active relay session in a browser
  imagine-mcp relay reset      Clear relay session + mode state
  imagine-mcp -h, --help       Show this help and exit
  imagine-mcp --version, -V    Show the installed version and exit

Credentials are set via the config__open_relay MCP tool (HTTP mode's browser
form) or the GEMINI_API_KEY / OPENAI_API_KEY / XAI_API_KEY env vars.
"""


def _serve(argv: list[str]) -> int | None:
    """Start the server -- stdio (default) or HTTP (--http / env opt-in).

    Transport dispatch unchanged from the pre-CLI ``__main__.main()``: stdio
    is env-only creds, single-user, no daemon/browser; HTTP is opt-in and
    always multi-user/remote-style (see ``imagine_mcp.server.run_http``).
    """
    is_http = (
        "--http" in argv
        or os.environ.get("MCP_TRANSPORT") == "http"
        or os.environ.get("TRANSPORT_MODE") == "http"
    )

    if is_http:
        from imagine_mcp.server import run_http

        asyncio.run(run_http())
        return None

    if not any(
        os.environ.get(k)
        for k in (
            "GEMINI_API_KEY",
            "OPENAI_API_KEY",
            "XAI_API_KEY",
            "GOOGLE_VERTEX_EXPRESS_API_KEY",
        )
    ):
        sys.stderr.write(_STDIO_MISSING_CRED_MSG)
        raise SystemExit(1)

    from imagine_mcp.server import build_app

    build_app().run(transport="stdio")
    return None


def _version() -> str:
    from imagine_mcp import __version__

    return __version__


def main() -> int:
    argv = sys.argv[1:]
    if argv[:1] == ["--version"] or argv[:1] == ["-V"]:
        print(_version())
        return 0
    if argv[:1] == ["-h"] or argv[:1] == ["--help"]:
        print(_HELP_TEXT, end="")
        return 0

    # build_cli's server_name doubles as the PerPluginStore/doctor identifier
    # (~/.{name}-mcp/config.json) -- it must be PLUGIN_NAME ("imagine"), the
    # same name save_credentials()/load_config_from_file() write through, not
    # the "imagine-mcp" console-script/package name. Passing the latter would
    # make `config status`/`doctor` silently check ~/.imagine-mcp-mcp/ (a path
    # nothing ever writes to) and always report "not configured".
    return build_cli(PLUGIN_NAME, serve=_serve, version=_version())(None)
