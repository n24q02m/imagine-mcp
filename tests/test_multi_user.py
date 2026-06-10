"""HTTP multi-user credential wiring (per-sub contextvar).

These tests cover the auth_scope + per-sub credential flow added so each
JWT subject sees only its own provider keys. Spec requirements:

* Stdio mode is unchanged (env-only, no contextvar leak).
* Single-user HTTP behaves like stdio for credential reads (no sub set).
* Multi-user HTTP scopes credentials per ``_current_sub`` ContextVar.
* The ``auth_scope`` middleware sets/resets the ContextVar around each request.
* PR #58's auto-fallback dispatcher (``_default_provider``) honours the
  per-sub keys instead of leaking ``os.environ``.
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

    The contextvar is None and ``credentials_for_current_request`` returns
    keys from ``os.environ`` -- NOT from PerPluginStore (matches the
    pure-env-only invariant guarded by ``feedback_stdio_fallback_local_only``).
    """
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.delenv("TRANSPORT_MODE", raising=False)
    monkeypatch.setattr("sys.argv", ["imagine-mcp"])

    monkeypatch.setenv("XAI_API_KEY", "stdio-xai")
    creds = credentials_for_current_request()
    assert creds == {"XAI_API_KEY": "stdio-xai"}
    assert get_current_sub() is None


def test_http_sub_a_isolation(tmp_path) -> None:
    """sub-a sees only sub-a's stored XAI key."""
    from mcp_core.storage.per_plugin_store import PerPluginStore

    PerPluginStore(PLUGIN_NAME, "sub-a").save({"XAI_API_KEY": "key-a"})
    PerPluginStore(PLUGIN_NAME, "sub-b").save({"OPENAI_API_KEY": "key-b"})

    set_current_sub("sub-a")
    creds = credentials_for_current_request()
    assert creds == {"XAI_API_KEY": "key-a"}
    assert "OPENAI_API_KEY" not in creds


def test_http_sub_b_no_bleed(tmp_path) -> None:
    """sub-b sees only sub-b's stored OPENAI key (no env or sub-a leak)."""
    from mcp_core.storage.per_plugin_store import PerPluginStore

    PerPluginStore(PLUGIN_NAME, "sub-a").save({"XAI_API_KEY": "key-a"})
    PerPluginStore(PLUGIN_NAME, "sub-b").save({"OPENAI_API_KEY": "key-b"})

    set_current_sub("sub-b")
    creds = credentials_for_current_request()
    assert creds == {"OPENAI_API_KEY": "key-b"}
    assert "XAI_API_KEY" not in creds


def test_http_no_sub_returns_env(monkeypatch) -> None:
    """HTTP mode + no sub set: helper merges os.environ (single-user fallback).

    Even though ``MCP_TRANSPORT=http`` is set, the contextvar may still be
    ``None`` for the local-credential-form authorize POST itself (it runs
    OUTSIDE the bearer-protected MCP route). We must therefore behave like
    stdio for credential reads when no sub is active.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "single-user-key")
    creds = credentials_for_current_request()
    assert creds == {"OPENAI_API_KEY": "single-user-key"}


def test_concurrent_subs_isolation(tmp_path) -> None:
    """Two ContextVar-aware coroutines must see independent sub state.

    Verifies that ``contextvars`` (not threading.local) is the correct
    choice -- asyncio tasks each have their own Context, so even
    interleaved suspensions cannot bleed sub-a's keys into sub-b's
    coroutine.
    """
    from mcp_core.storage.per_plugin_store import PerPluginStore

    PerPluginStore(PLUGIN_NAME, "sub-a").save({"XAI_API_KEY": "key-a"})
    PerPluginStore(PLUGIN_NAME, "sub-b").save({"OPENAI_API_KEY": "key-b"})

    captured: dict[str, dict[str, str]] = {}

    async def request_for(sub: str) -> None:
        token = _current_sub.set(sub)
        try:
            # Yield control so the other coroutine interleaves between
            # set() and read().
            await asyncio.sleep(0)
            captured[sub] = credentials_for_current_request()
        finally:
            _current_sub.reset(token)

    async def driver() -> None:
        await asyncio.gather(request_for("sub-a"), request_for("sub-b"))

    asyncio.run(driver())

    assert captured["sub-a"] == {"XAI_API_KEY": "key-a"}
    assert captured["sub-b"] == {"OPENAI_API_KEY": "key-b"}


def test_per_request_sub_scope_callback(tmp_path) -> None:
    """The ``_per_request_sub_scope`` middleware sets + resets _current_sub.

    Mirrors the ``auth_scope`` callback signature mcp-core invokes after
    JWT verification. Ensures (a) the contextvar carries the sub during
    ``next_()``, (b) it resets to None even if ``next_()`` raises.
    """
    from imagine_mcp.server import _per_request_sub_scope

    seen: list[str | None] = []

    async def _next_ok() -> None:
        seen.append(get_current_sub())

    async def driver() -> None:
        await _per_request_sub_scope({"sub": "user-42"}, _next_ok)
        # After the middleware returns, the contextvar must be reset.
        seen.append(get_current_sub())

    asyncio.run(driver())
    assert seen == ["user-42", None]

    # Failure path: middleware must reset the contextvar even when
    # next_() raises so the next request handled by this asyncio task
    # cannot inherit a stale sub.
    async def _next_raises() -> None:
        seen.append(get_current_sub())
        raise RuntimeError("boom")

    seen.clear()

    async def driver_raises() -> None:
        with pytest.raises(RuntimeError, match="boom"):
            await _per_request_sub_scope({"sub": "user-99"}, _next_raises)
        seen.append(get_current_sub())

    asyncio.run(driver_raises())
    assert seen == ["user-99", None]


def test_default_provider_with_per_sub_keys(tmp_path) -> None:
    """PR #58 auto-fallback honours per-sub keys, not os.environ.

    sub-grok holds only XAI -> dispatcher must pick ``grok``.
    sub-openai holds only OPENAI -> dispatcher must pick ``openai``.
    sub-gemini holds only GEMINI -> dispatcher must pick ``gemini``.
    A sub with no keys must raise ``CredentialMissingError``.
    """
    from mcp_core.storage.per_plugin_store import PerPluginStore

    from imagine_mcp.dispatcher import _default_provider
    from imagine_mcp.errors import CredentialMissingError

    PerPluginStore(PLUGIN_NAME, "sub-grok").save({"XAI_API_KEY": "k1"})
    PerPluginStore(PLUGIN_NAME, "sub-openai").save({"OPENAI_API_KEY": "k2"})
    PerPluginStore(PLUGIN_NAME, "sub-gemini").save({"GEMINI_API_KEY": "k3"})
    PerPluginStore(PLUGIN_NAME, "sub-empty").save({})

    set_current_sub("sub-grok")
    assert _default_provider() == "grok"

    set_current_sub("sub-openai")
    assert _default_provider() == "openai"

    set_current_sub("sub-gemini")
    assert _default_provider() == "gemini"

    set_current_sub("sub-empty")
    with pytest.raises(CredentialMissingError):
        _default_provider()


def test_default_provider_priority_xai_over_openai(tmp_path) -> None:
    """When a sub has multiple keys, XAI > OPENAI > GEMINI per PR #58."""
    from mcp_core.storage.per_plugin_store import PerPluginStore

    from imagine_mcp.dispatcher import _default_provider

    PerPluginStore(PLUGIN_NAME, "sub-multi").save(
        {"XAI_API_KEY": "x", "OPENAI_API_KEY": "o", "GEMINI_API_KEY": "g"}
    )

    set_current_sub("sub-multi")
    assert _default_provider() == "grok"


def test_provider_client_isolated_per_sub(tmp_path, monkeypatch) -> None:
    """Provider clients cache per-sub so concurrent users get distinct keys.

    Verifies the ``_SUB_CLIENTS`` map: each sub builds its own client wired
    to that sub's API key, and switching back to a different sub returns
    that sub's cached client (not a shared module-level client).
    """
    from mcp_core.storage.per_plugin_store import PerPluginStore

    from imagine_mcp.providers import gemini

    captured: list[str] = []

    class _FakeClient:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key
            captured.append(api_key)

    class _FakeGenaiModule:
        Client = _FakeClient

    monkeypatch.setitem(
        __import__("sys").modules, "google", type("g", (), {"genai": _FakeGenaiModule})
    )

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
    assert client_a.api_key == "ga"
    assert client_b.api_key == "gb"
    # Each sub triggers exactly one client construction.
    assert captured.count("ga") == 1
    assert captured.count("gb") == 1
