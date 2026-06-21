"""Sub-aware model-chain + generate-selection resolution.

Multi-user HTTP mode stores the relay-submitted ``UNDERSTAND_MODELS`` /
``GENERATE_MODELS`` / ``GENERATE_PROVIDER_PRIORITY`` per JWT subject (never in
``os.environ`` -- that would leak one sub's chain to a concurrent request of
another sub). These tests pin that the resolvers read the per-sub config when a
sub is active and fall back to ``os.environ`` only in single-user / stdio mode.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest

from imagine_mcp.credential_state import (
    CLOUD_KEYS,
    _current_sub,
    set_current_sub,
    store_for_sub,
)
from imagine_mcp.dispatcher import (
    _DEFAULT_PROVIDER_PRIORITY,
    resolve_generate_chain,
    resolve_generate_provider_priority,
    resolve_understand_chain,
)


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch) -> Iterator[None]:
    """Pin PerPluginStore, force HTTP mode, clear chain + key env vars."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-secret-value")
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    for key in (
        *CLOUD_KEYS,
        "UNDERSTAND_MODELS",
        "GENERATE_MODELS",
        "GENERATE_PROVIDER_PRIORITY",
    ):
        monkeypatch.delenv(key, raising=False)
    token = _current_sub.set(None)
    yield
    _current_sub.reset(token)


# ---------------------------------------------------------------------------
# Fix 1: sub-aware UNDERSTAND_MODELS chain
# ---------------------------------------------------------------------------
def test_understand_chain_reads_per_sub_config() -> None:
    """A sub's stored UNDERSTAND_MODELS reaches resolve_understand_chain()."""
    store_for_sub(
        "sub-a",
        {"UNDERSTAND_MODELS": "xai/grok-4.20-0309-non-reasoning,gemini/flash"},
    )
    set_current_sub("sub-a")
    assert resolve_understand_chain() == [
        "xai/grok-4.20-0309-non-reasoning",
        "gemini/flash",
    ]


def test_understand_chain_other_sub_does_not_see_first() -> None:
    """A different sub does NOT inherit the first sub's chain."""
    store_for_sub("sub-a", {"UNDERSTAND_MODELS": "xai/grok-a"})
    store_for_sub("sub-b", {"UNDERSTAND_MODELS": "openai/gpt-b"})

    set_current_sub("sub-a")
    assert resolve_understand_chain() == ["xai/grok-a"]

    set_current_sub("sub-b")
    assert resolve_understand_chain() == ["openai/gpt-b"]


def test_understand_chain_sub_without_config_is_empty() -> None:
    """A sub with no stored chain resolves to an empty list (not env leak)."""
    store_for_sub("sub-a", {"UNDERSTAND_MODELS": "xai/grok-a"})
    set_current_sub("sub-b")
    assert resolve_understand_chain() == []


def test_understand_chain_does_not_write_os_environ() -> None:
    """Resolving a per-sub chain must never mutate the process-global env."""
    import os

    store_for_sub("sub-a", {"UNDERSTAND_MODELS": "xai/grok-a"})
    set_current_sub("sub-a")
    resolve_understand_chain()
    assert "UNDERSTAND_MODELS" not in os.environ


def test_understand_chain_single_user_reads_env(monkeypatch) -> None:
    """No sub set (single-user/stdio): falls back to os.getenv."""
    set_current_sub(None)
    monkeypatch.setenv("UNDERSTAND_MODELS", "gemini/from-env")
    assert resolve_understand_chain() == ["gemini/from-env"]


# ---------------------------------------------------------------------------
# Fix 2: sub-aware GENERATE_MODELS chain
# ---------------------------------------------------------------------------
def test_generate_chain_reads_per_sub_config() -> None:
    store_for_sub(
        "sub-a",
        {"GENERATE_MODELS": "gemini/imagen-x,openai/gpt-image-y"},
    )
    set_current_sub("sub-a")
    assert resolve_generate_chain() == ["gemini/imagen-x", "openai/gpt-image-y"]


def test_generate_chain_other_sub_does_not_see_first() -> None:
    store_for_sub("sub-a", {"GENERATE_MODELS": "gemini/gen-a"})
    store_for_sub("sub-b", {})

    set_current_sub("sub-a")
    assert resolve_generate_chain() == ["gemini/gen-a"]

    set_current_sub("sub-b")
    assert resolve_generate_chain() == []


def test_generate_chain_single_user_reads_env(monkeypatch) -> None:
    set_current_sub(None)
    monkeypatch.setenv("GENERATE_MODELS", "grok/grok-imagine-image")
    assert resolve_generate_chain() == ["grok/grok-imagine-image"]


def test_generate_chain_empty_unset(monkeypatch) -> None:
    set_current_sub(None)
    monkeypatch.delenv("GENERATE_MODELS", raising=False)
    assert resolve_generate_chain() == []


# ---------------------------------------------------------------------------
# Fix 2: sub-aware GENERATE_PROVIDER_PRIORITY
# ---------------------------------------------------------------------------
def test_generate_provider_priority_default_is_catalog_tuple() -> None:
    """Unset -> the existing _DEFAULT_PROVIDER_PRIORITY order."""
    set_current_sub(None)
    expected = [provider for _env, provider in _DEFAULT_PROVIDER_PRIORITY]
    assert resolve_generate_provider_priority() == expected


def test_generate_provider_priority_per_sub_override() -> None:
    store_for_sub("sub-a", {"GENERATE_PROVIDER_PRIORITY": "gemini,openai,grok"})
    set_current_sub("sub-a")
    assert resolve_generate_provider_priority() == ["gemini", "openai", "grok"]


def test_generate_provider_priority_single_user_env(monkeypatch) -> None:
    set_current_sub(None)
    monkeypatch.setenv("GENERATE_PROVIDER_PRIORITY", "openai,grok,gemini")
    assert resolve_generate_provider_priority() == ["openai", "grok", "gemini"]


def test_generate_provider_priority_concurrent_subs_isolated() -> None:
    """Two coroutines with distinct subs see independent priorities."""
    store_for_sub("sub-a", {"GENERATE_PROVIDER_PRIORITY": "gemini,openai,grok"})
    store_for_sub("sub-b", {"GENERATE_PROVIDER_PRIORITY": "grok,openai,gemini"})

    captured: dict[str, list[str]] = {}

    async def request_for(sub: str) -> None:
        token = _current_sub.set(sub)
        try:
            await asyncio.sleep(0)
            captured[sub] = resolve_generate_provider_priority()
        finally:
            _current_sub.reset(token)

    async def driver() -> None:
        await asyncio.gather(request_for("sub-a"), request_for("sub-b"))

    asyncio.run(driver())
    assert captured["sub-a"] == ["gemini", "openai", "grok"]
    assert captured["sub-b"] == ["grok", "openai", "gemini"]
