"""Tests for the ``__main__`` entry point mode dispatch.

``main()`` picks stdio vs http and, in stdio mode, hard-exits when no
provider key is configured (the server has no usable tools without one).
"""

from __future__ import annotations

import sys

import pytest

from imagine_mcp.__main__ import main

_CRED_KEYS = ("GEMINI_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY")
_MODE_KEYS = ("MCP_TRANSPORT", "TRANSPORT_MODE")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in (*_CRED_KEYS, *_MODE_KEYS):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(sys, "argv", ["imagine-mcp"])
    yield


def test_stdio_mode_exits_when_no_credentials(monkeypatch, capsys):
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert "No provider API keys set" in capsys.readouterr().err


def test_stdio_mode_runs_app_when_credential_present(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    calls: dict[str, object] = {}

    class _App:
        def run(self, *, transport):
            calls["transport"] = transport

    monkeypatch.setattr("imagine_mcp.server.build_app", lambda: _App())
    main()
    assert calls == {"transport": "stdio"}


@pytest.mark.parametrize(
    ("argv", "env"),
    [
        (["imagine-mcp", "--http"], None),
        (["imagine-mcp"], ("MCP_TRANSPORT", "http")),
        (["imagine-mcp"], ("TRANSPORT_MODE", "http")),
    ],
)
def test_http_mode_dispatch(monkeypatch, argv, env):
    monkeypatch.setattr(sys, "argv", argv)
    if env is not None:
        monkeypatch.setenv(*env)
    called = False

    async def _run_http():
        nonlocal called
        called = True

    monkeypatch.setattr("imagine_mcp.server.run_http", _run_http)
    main()
    assert called is True
