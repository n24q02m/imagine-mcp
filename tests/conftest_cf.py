"""Cloudflare-pilot test fixtures for imagine-mcp (KV-only): a deterministic
KV http double + canonical CF/local env presets. Ported (KV slice only) from
wet-mcp/tests/conftest_cf.py."""

from __future__ import annotations

import pytest


class FakeKvHttp:
    """Injectable http for mcp_core CfKvBackend.

    Implements ``.request(method, url, data, headers) -> (status, body)``
    exactly as CfKvBackend expects (URL-encoded single-segment key).
    """

    def __init__(self) -> None:
        self.store: dict[str, bytes] = {}

    def request(self, method, url, data=None, headers=None):
        from urllib.parse import unquote

        key = unquote(url.rsplit("/", 1)[-1])
        if method == "PUT":
            self.store[key] = data or b""
            return (200, b"")
        if method == "GET":
            return (200, self.store[key]) if key in self.store else (404, b"")
        if method == "DELETE":
            existed = key in self.store
            self.store.pop(key, None)
            return (200, b"") if existed else (404, b"")
        raise AssertionError(f"unexpected method {method}")


@pytest.fixture
def fake_kv_http():
    return FakeKvHttp()


@pytest.fixture
def cf_env(monkeypatch):
    """Canonical CF env preset; secrets are dummies (never inline real ones)."""
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.setenv("CREDENTIAL_SECRET", "test-credential-secret")
    monkeypatch.setenv("MCP_STORAGE_BACKEND", "cf-kv")
    monkeypatch.setenv("MCP_KV_BASE_URL", "http://kv.internal")
    monkeypatch.setenv("IMAGINE_OUTPUT_MODE", "base64")


@pytest.fixture
def local_default_env(monkeypatch):
    """Back-compat: no CF env -> LocalFs + on-disk media path."""
    for var in ("MCP_STORAGE_BACKEND", "MCP_KV_BASE_URL", "IMAGINE_OUTPUT_MODE"):
        monkeypatch.delenv(var, raising=False)
