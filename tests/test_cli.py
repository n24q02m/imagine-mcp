"""Tests for imagine_mcp.cli -- shared mcp_core CLI builder mount (W5.1).

Bare invocation and any leading-dash argv start the server unchanged (the
stdio/--http dispatch that used to live directly in ``__main__.main()`` moved
into ``_serve`` here without behaviour changes); ``build_cli`` fronts it with
``config``/``relay``/``doctor`` subcommand routing. ``--version``/``-h`` are
handled before ``build_cli`` ever sees them: ``mcp_core.cli.build_cli`` passes
every leading-dash argv straight through to ``serve`` (it does not special-
case ``--version``/``-h`` itself -- see ``mcp_core/cli.py`` module docstring),
so without this interception ``imagine-mcp --version`` would start the stdio
server and hang on stdin instead of printing a version and exiting.
"""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from imagine_mcp import __version__

_CRED_KEYS = (
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "XAI_API_KEY",
    "GOOGLE_VERTEX_EXPRESS_API_KEY",
)
_MODE_KEYS = ("MCP_TRANSPORT", "TRANSPORT_MODE")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in (*_CRED_KEYS, *_MODE_KEYS):
        monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture
def cli_storage(tmp_path, monkeypatch):
    """Redirect PerPluginStore (``Path.home``) and the relay session lock
    (``mcp_core`` ``set_lock_dir``) into ``tmp_path`` so the built-in
    ``config``/``relay``/``doctor`` subcommand tests never touch the real
    user home directory. Mirrors mcp-core's own ``cli_storage`` fixture in
    ``packages/core-py/tests/test_cli.py``.
    """
    from mcp_core.storage.session_lock import set_lock_dir

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    set_lock_dir(str(tmp_path / "locks"))
    yield tmp_path
    set_lock_dir(None)


class TestServeDispatch:
    """Bare/flag argv route to ``_serve`` (stdio/--http) unchanged."""

    def test_bare_invocation_exits_1_without_credentials(self, capsys):
        from imagine_mcp import cli

        with (
            patch.object(sys, "argv", ["imagine-mcp"]),
            pytest.raises(SystemExit) as exc,
        ):
            cli.main()

        assert exc.value.code == 1
        assert "No provider API keys set" in capsys.readouterr().err

    def test_bare_invocation_runs_stdio_when_credential_present(self, monkeypatch):
        from imagine_mcp import cli

        monkeypatch.setenv("OPENAI_API_KEY", "key")
        calls: dict[str, object] = {}

        class _App:
            def run(self, *, transport):
                calls["transport"] = transport

        monkeypatch.setattr("imagine_mcp.server.build_app", lambda: _App())
        with patch.object(sys, "argv", ["imagine-mcp"]):
            rc = cli.main()

        assert rc == 0
        assert calls == {"transport": "stdio"}

    def test_http_flag_passes_through_and_starts_http_mode(self, monkeypatch):
        from imagine_mcp import cli

        called = False

        async def _run_http():
            nonlocal called
            called = True

        monkeypatch.setattr("imagine_mcp.server.run_http", _run_http)
        with patch.object(sys, "argv", ["imagine-mcp", "--http"]):
            rc = cli.main()

        assert rc == 0
        assert called is True

    @pytest.mark.parametrize("env_key", ["MCP_TRANSPORT", "TRANSPORT_MODE"])
    def test_transport_env_starts_http_mode(self, monkeypatch, env_key):
        from imagine_mcp import cli

        monkeypatch.setenv(env_key, "http")
        called = False

        async def _run_http():
            nonlocal called
            called = True

        monkeypatch.setattr("imagine_mcp.server.run_http", _run_http)
        with patch.object(sys, "argv", ["imagine-mcp"]):
            rc = cli.main()

        assert rc == 0
        assert called is True


class TestVersionAndHelp:
    """The gap this task closes: imagine-mcp had no --version/-h at all."""

    def test_version_flag_prints_and_exits_0(self, capsys):
        from imagine_mcp import cli

        with patch.object(sys, "argv", ["imagine-mcp", "--version"]):
            rc = cli.main()

        assert rc == 0
        assert capsys.readouterr().out.strip() == __version__

    def test_short_version_flag(self, capsys):
        from imagine_mcp import cli

        with patch.object(sys, "argv", ["imagine-mcp", "-V"]):
            rc = cli.main()

        assert rc == 0
        assert capsys.readouterr().out.strip() == __version__

    def test_help_flag_prints_usage_and_exits_0(self, capsys):
        from imagine_mcp import cli

        with patch.object(sys, "argv", ["imagine-mcp", "-h"]):
            rc = cli.main()

        assert rc == 0
        out = capsys.readouterr().out
        assert "imagine-mcp" in out
        assert "doctor" in out
        assert "config status" in out
        assert "relay" in out

    def test_long_help_flag(self, capsys):
        from imagine_mcp import cli

        with patch.object(sys, "argv", ["imagine-mcp", "--help"]):
            rc = cli.main()

        assert rc == 0
        assert "Usage:" in capsys.readouterr().out


class TestBuiltinSubcommands:
    """``config``/``relay``/``doctor`` are ``mcp_core.cli`` built-ins.

    The critical correctness property under test: ``build_cli``'s
    ``server_name`` identifier must match ``relay_setup.PLUGIN_NAME``
    (``"imagine"``), NOT the ``imagine-mcp`` console-script/package name.
    ``PerPluginStore`` keys its on-disk path off that name
    (``~/.{name}-mcp/config.json``) -- passing ``"imagine-mcp"`` (as the
    wet-mcp/better-telegram-mcp CLI wiring does for their own SERVER_NAME)
    would make ``config status``/``doctor`` silently inspect
    ``~/.imagine-mcp-mcp/`` (double suffix), a path nothing ever writes to,
    so they would always report "not configured" even when the server is
    actually configured. These tests would fail if that mismatch were
    reintroduced.
    """

    def test_config_status_reflects_real_saved_credentials(self, cli_storage, capsys):
        from mcp_core.storage.per_plugin_store import PerPluginStore

        from imagine_mcp.relay_setup import PLUGIN_NAME

        PerPluginStore(PLUGIN_NAME).save({"GEMINI_API_KEY": "test-key"})

        from imagine_mcp import cli

        with patch.object(sys, "argv", ["imagine-mcp", "config", "status"]):
            rc = cli.main()

        assert rc == 0
        out = capsys.readouterr().out
        assert "configured" in out
        assert "not configured" not in out
        assert "test-key" not in out

    def test_config_status_not_configured(self, cli_storage, capsys):
        from imagine_mcp import cli

        with patch.object(sys, "argv", ["imagine-mcp", "config", "status"]):
            rc = cli.main()

        assert rc == 0
        assert "not configured" in capsys.readouterr().out

    def test_config_delete_with_yes_deletes_real_store(self, cli_storage):
        from mcp_core.storage.per_plugin_store import PerPluginStore

        from imagine_mcp.relay_setup import PLUGIN_NAME

        PerPluginStore(PLUGIN_NAME).save({"GEMINI_API_KEY": "test-key"})

        from imagine_mcp import cli

        with patch.object(sys, "argv", ["imagine-mcp", "config", "delete", "--yes"]):
            rc = cli.main()

        assert rc == 0
        assert PerPluginStore(PLUGIN_NAME).load() is None

    def test_doctor_reports_real_configured_state(self, cli_storage, capsys):
        from mcp_core.storage.per_plugin_store import PerPluginStore

        from imagine_mcp.relay_setup import PLUGIN_NAME

        PerPluginStore(PLUGIN_NAME).save({"GEMINI_API_KEY": "test-key"})

        from imagine_mcp import cli

        with patch.object(sys, "argv", ["imagine-mcp", "doctor"]):
            rc = cli.main()

        out = capsys.readouterr().out
        assert rc == 0
        assert "[ok] config: configured" in out
        assert "[warn] config: not configured" not in out

    def test_doctor_healthy_when_unconfigured(self, cli_storage, capsys):
        from imagine_mcp import cli

        with patch.object(sys, "argv", ["imagine-mcp", "doctor"]):
            rc = cli.main()

        out = capsys.readouterr().out
        assert rc == 0
        assert "[fail]" not in out
        assert "[warn] config: not configured" in out

    def test_relay_status_reports_no_active_session(self, cli_storage, capsys):
        from imagine_mcp import cli

        with patch.object(sys, "argv", ["imagine-mcp", "relay", "status"]):
            rc = cli.main()

        assert rc == 1
        assert "no active relay session" in capsys.readouterr().err

    def test_unknown_subcommand_lists_builtins(self, capsys):
        from imagine_mcp import cli

        with patch.object(sys, "argv", ["imagine-mcp", "bogus"]):
            rc = cli.main()

        assert rc == 2
        err = capsys.readouterr().err
        assert "config" in err
        assert "relay" in err
        assert "doctor" in err
