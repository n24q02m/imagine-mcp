"""Tests for imagine_mcp.__main__ -- thin wrapper delegating to imagine_mcp.cli.main.

Dispatch (bare/--http/env-mode/--version/-h/config/relay/doctor) is exercised
in tests/test_cli.py against the real mcp_core build_cli builder; this only
verifies the delegation wiring for `python -m imagine_mcp` / the console
script (mirrors better-telegram-mcp's tests/test_main.py::TestCli).
"""

from __future__ import annotations

from unittest.mock import patch


def test_delegates_to_cli_main():
    from imagine_mcp.__main__ import _cli

    with patch("imagine_mcp.__main__._cli_main", return_value=0) as mock_cli_main:
        rc = _cli()

    mock_cli_main.assert_called_once_with()
    assert rc == 0
