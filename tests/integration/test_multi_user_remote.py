"""Per-sub LLM key isolation in imagine-mcp remote multi-user mode.

Multi-user remote is an HTTP-mode deployment property (spec 2026-05-01
§4.2). Stdio mode never reads from PerPluginStore, so these tests must
opt into HTTP mode via ``MCP_TRANSPORT=http`` for ``read_for_sub`` to
return the stored credentials.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _force_http_mode(monkeypatch):
    monkeypatch.setenv("MCP_TRANSPORT", "http")


@pytest.mark.integration
def test_two_subs_isolated(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-secret-value")
    from imagine_mcp.credential_state import read_for_sub, store_for_sub

    store_for_sub("user_a", {"GEMINI_API_KEY": "key_a"})
    store_for_sub("user_b", {"GEMINI_API_KEY": "key_b"})

    assert read_for_sub("user_a")["GEMINI_API_KEY"] == "key_a"
    assert read_for_sub("user_b")["GEMINI_API_KEY"] == "key_b"


@pytest.mark.integration
def test_save_credentials_uses_sub_when_public_url_set(tmp_path, monkeypatch):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-secret-value")
    monkeypatch.setenv("PUBLIC_URL", "https://imagine.example.com")
    from imagine_mcp.credential_state import read_for_sub, save_credentials

    save_credentials({"GEMINI_API_KEY": "k1"}, {"sub": "user_a"})
    save_credentials({"GEMINI_API_KEY": "k2"}, {"sub": "user_b"})

    assert read_for_sub("user_a")["GEMINI_API_KEY"] == "k1"
    assert read_for_sub("user_b")["GEMINI_API_KEY"] == "k2"
