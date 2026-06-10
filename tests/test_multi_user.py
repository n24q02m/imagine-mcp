"""HTTP multi-user credential wiring (per-sub contextvar).

These tests cover the auth_scope + per-sub credential flow added so each
JWT subject sees only its own provider keys. Spec requirements:

* Stdio mode is unchanged (env-only, no contextvar leak).
* Single-user HTTP behaves like stdio for credential reads (no sub set).
* Multi-user HTTP scopes credentials per `*`*_current_sub`*`* ContextVar.
* The `*`*auth_scope`*`* middleware sets/resets the ContextVar around each request.
* PR #58's auto-fallback dispatcher (`*`*_default_provider`**) honours the
  per-sub keys instead of leaking `*`*os.environ`*`*.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest

from imagine_mcp.credential_state import (
    CLOUD_KEYS,
    PLUGIN_NAME,
    _current_sub,
    credentials_for_current_request,
    get_current_sub,
    set_current_sub,
)


@pytest.fixture(autouse=True)
def _isolate_storage(tmp_path, monkeypatch) -> Iterator[None]:
    """Pin PerPluginStore + reset contextvar before every test."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-secret-value")
    # Force HTTP mode so credential_state helpers touch PerPluginStore.
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    # Make sure no env-leak into per-sub assertions.
    for key in CLOUD_KEYS:
        monkeypatch.delenv(key, raising=False)
    # Reset contextvar state.
    token = _current_sub.set(None)
    yield
    _current_sub.reset(token)


def test_stdio_mode_unchanged(monkeypatch) -> None:
    """Stdio mode (no --http, no transport env): env vars only.

    The contextvar is None and `*`*credentials_for_current_request`*`* returns
    os.environ (standard stdio behavior).
    """
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")

    assert get_current_sub() is None
    assert credentials_for_current_request().get("GEMINI_API_KEY") == "env-key"


def test_single_user_http_mode(monkeypatch) -> None:
    """HTTP transport with no sub set: behaves like stdio (env vars)."""
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")

    assert get_current_sub() is None
    # No sub active -> fall back to env.
    assert credentials_for_current_request().get("GEMINI_API_KEY") == "env-key"


def test_multi_user_isolation(tmp_path, monkeypatch) -> None:
    """Credentials from PerPluginStore are scoped to the active sub."""
    from mcp_core.storage.per_plugin_store import PerPluginStore

    # User A key
    PerPluginStore(PLUGIN_NAME, "sub-a").save({"GEMINI_API_KEY": "key-a"})
    # User B key
    PerPluginStore(PLUGIN_NAME, "sub-b").save({"GEMINI_API_KEY": "key-b"})

    # Switch to User A
    set_current_sub("sub-a")
    assert credentials_for_current_request().get("GEMINI_API_KEY") == "key-a"

    # Switch to User B
    set_current_sub("sub-b")
    assert credentials_for_current_request().get("GEMINI_API_KEY") == "key-b"

    # Switch back to None (single-user / system request)
    set_current_sub(None)
    assert credentials_for_current_request().get("GEMINI_API_KEY") is None


def test_multi_user_env_leak_prevention(tmp_path, monkeypatch) -> None:
    """Active sub MUST NOT see os.environ keys (isolation requirement)."""
    from mcp_core.storage.per_plugin_store import PerPluginStore

    # Set a global key in environment.
    monkeypatch.setenv("GEMINI_API_KEY", "global-key")

    # User has NO keys in storage.
    PerPluginStore(PLUGIN_NAME, "sub-empty").save({})

    set_current_sub("sub-empty")
    # Should NOT fall back to environment.
    assert credentials_for_current_request().get("GEMINI_API_KEY") is None


def test_concurrent_subs_leak_prevention(tmp_path, monkeypatch) -> None:
    """Verify contextvars isolation using asyncio tasks with different subs."""
    from mcp_core.storage.per_plugin_store import PerPluginStore

    PerPluginStore(PLUGIN_NAME, "sub-1").save({"GEMINI_API_KEY": "k1"})
    PerPluginStore(PLUGIN_NAME, "sub-2").save({"GEMINI_API_KEY": "k2"})

    async def check_sub(sub, expected):
        set_current_sub(sub)
        # Yield to event loop to allow other tasks to run.
        await asyncio.sleep(0.01)
        assert credentials_for_current_request().get("GEMINI_API_KEY") == expected

    async def main():
        await asyncio.gather(
            check_sub("sub-1", "k1"),
            check_sub("sub-2", "k2"),
        )

    asyncio.run(main())


def test_default_provider_honours_per_sub(tmp_path, monkeypatch) -> None:
    """dispatcher._default_provider must look at per-sub creds."""
    from mcp_core.storage.per_plugin_store import PerPluginStore

    from imagine_mcp.dispatcher import _default_provider

    # Env has OpenAI.
    monkeypatch.setenv("OPENAI_API_KEY", "o-env")

    # sub-multi has ONLY Grok in PerPluginStore.
    PerPluginStore(PLUGIN_NAME, "sub-multi").save(
        {"XAI_API_KEY": "x-sub", "OPENAI_API_KEY": ""}
    )

    set_current_sub("sub-multi")
    assert _default_provider() == "grok"


def test_provider_client_isolated_per_sub(tmp_path, monkeypatch) -> None:
    """Provider clients cache per-sub so concurrent users get distinct keys.

    Verifies the `*`*_SUB_CLIENTS`*`* map: each sub builds its own client wired
    to that sub's API key, and switching back to a different sub returns
    that sub's cached client (not a shared module-level client).
    """
    # We need to monkeypatch the 'genai' import within imagine_mcp.providers.gemini
    # But since it's already imported at top-level now, we patch the module itself.
    import google.genai as genai_mod
    from mcp_core.storage.per_plugin_store import PerPluginStore

    captured: list[str] = []

    class _FakeClient:
        def __init__(self, api_key: str) -> None:
            self._mcp_test_api_key = api_key
            captured.append(api_key)

    monkeypatch.setattr(genai_mod, "Client", _FakeClient)

    from imagine_mcp.providers import gemini

    PerPluginStore(PLUGIN_NAME, "sub-a").save({"GEMINI_API_KEY": "ga"})
    PerPluginStore(PLUGIN_NAME, "sub-b").save({"GEMINI_API_KEY": "gb"})

    gemini._reset_client()

    set_current_sub("sub-a")
    client_a = gemini._client()
    set_current_sub("sub-b")
    client_b = gemini._client()
    set_current_sub("sub-a")
    client_a_again = gemini._client()

    assert client_a is client_a_again
    assert client_a is not client_b
    assert getattr(client_a, "_mcp_test_api_key", None) == "ga"
    assert getattr(client_b, "_mcp_test_api_key", None) == "gb"
    # Each sub triggers exactly one client construction.
    assert captured.count("ga") == 1
    assert captured.count("gb") == 1
