"""Tests for relay onboarding: config resolution, persistence, reset.

``relay_setup`` decides whether the server prompts for credentials via the
browser relay or starts in degraded mode. The resolution order
(env -> per-plugin store -> relay -> degraded) is load-bearing, so each
branch is pinned here.
"""

from __future__ import annotations

import pytest

from imagine_mcp import relay_setup
from imagine_mcp.relay_setup import (
    apply_config,
    ensure_config,
    load_config_from_file,
    reset_credentials,
    save_credentials,
)

_CRED_KEYS = ("GEMINI_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY")


@pytest.fixture(autouse=True)
def _isolate(monkeypatch, tmp_path):
    """Isolate per-plugin store to tmp_path and clear credential env vars.

    ``monkeypatch.delenv`` records the absent state, so any env var the code
    under test writes directly to ``os.environ`` is also torn down.
    """
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    for key in (*_CRED_KEYS, "MCP_RELAY_URL"):
        monkeypatch.delenv(key, raising=False)
    yield


def _store():
    from mcp_core.storage.per_plugin_store import PerPluginStore

    return PerPluginStore(relay_setup.PLUGIN_NAME)


# --------------------------------------------------------------------------
# load_config_from_file
# --------------------------------------------------------------------------
def test_load_config_returns_none_when_store_empty():
    assert load_config_from_file() is None


def test_load_config_returns_saved_credentials():
    _store().save({"GEMINI_API_KEY": "gk"})
    assert load_config_from_file() == {"GEMINI_API_KEY": "gk"}


def test_load_config_returns_none_when_store_has_no_credential_keys():
    _store().save({"UNRELATED": "x"})
    assert load_config_from_file() is None


# --------------------------------------------------------------------------
# apply_config
# --------------------------------------------------------------------------
def test_apply_config_sets_missing_env(monkeypatch):
    apply_config({"OPENAI_API_KEY": "ok"})
    import os

    assert os.environ["OPENAI_API_KEY"] == "ok"


def test_apply_config_does_not_overwrite_existing_env(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "original")
    apply_config({"XAI_API_KEY": "replacement"})
    import os

    assert os.environ["XAI_API_KEY"] == "original"


def test_apply_config_skips_empty_values():
    apply_config({"GEMINI_API_KEY": ""})
    import os

    assert "GEMINI_API_KEY" not in os.environ


# --------------------------------------------------------------------------
# save_credentials
# --------------------------------------------------------------------------
def test_save_credentials_persists_and_applies():
    result = save_credentials({"GEMINI_API_KEY": "saved"})
    assert result is None
    import os

    assert os.environ["GEMINI_API_KEY"] == "saved"
    assert _store().load() == {"GEMINI_API_KEY": "saved"}


# --------------------------------------------------------------------------
# ensure_config
# --------------------------------------------------------------------------
async def test_ensure_config_skips_relay_when_env_present(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    assert await ensure_config() is None


async def test_ensure_config_uses_saved_config_file():
    _store().save({"OPENAI_API_KEY": "from-file"})
    config = await ensure_config()
    assert config == {"OPENAI_API_KEY": "from-file"}
    import os

    assert os.environ["OPENAI_API_KEY"] == "from-file"


async def test_ensure_config_degraded_when_no_creds_and_no_relay_url():
    assert await ensure_config() is None


async def test_ensure_config_returns_none_when_relay_fails(monkeypatch):
    monkeypatch.setenv("MCP_RELAY_URL", "https://relay.invalid")

    async def _boom(*_args, **_kwargs):
        raise RuntimeError("relay unreachable")

    monkeypatch.setattr("mcp_core.relay.client.create_session", _boom)
    assert await ensure_config() is None


async def test_ensure_config_relay_success_persists_config(monkeypatch):
    monkeypatch.setenv("MCP_RELAY_URL", "https://relay.example")

    class _Session:
        relay_url = "https://relay.example/authorize/abc"

    async def _create_session(*_args, **_kwargs):
        return _Session()

    async def _poll(*_args, **_kwargs):
        return {"XAI_API_KEY": "relayed"}

    monkeypatch.setattr("mcp_core.relay.client.create_session", _create_session)
    monkeypatch.setattr("mcp_core.relay.client.poll_for_result", _poll)

    config = await ensure_config()
    assert config == {"XAI_API_KEY": "relayed"}
    assert _store().load() == {"XAI_API_KEY": "relayed"}


# --------------------------------------------------------------------------
# reset_credentials
# --------------------------------------------------------------------------
def test_reset_credentials_not_found_when_no_config():
    assert reset_credentials() == {
        "status": "not_found",
        "server": relay_setup.SERVER_NAME,
    }


def test_reset_credentials_clears_existing_store():
    save_credentials({"GEMINI_API_KEY": "x"})
    assert reset_credentials() == {
        "status": "reset",
        "server": relay_setup.SERVER_NAME,
    }
    assert _store().load() is None
