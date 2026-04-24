from __future__ import annotations

import time
from pathlib import Path

from imagine_mcp.cache import ResponseCache


def test_set_and_get(tmp_path: Path) -> None:
    cache = ResponseCache(path=tmp_path / "cache", default_ttl=60)
    cache.set("key1", {"data": "value"})
    assert cache.get("key1") == {"data": "value"}


def test_miss_returns_none(tmp_path: Path) -> None:
    cache = ResponseCache(path=tmp_path / "cache", default_ttl=60)
    assert cache.get("nonexistent") is None


def test_ttl_expiry(tmp_path: Path) -> None:
    cache = ResponseCache(path=tmp_path / "cache", default_ttl=1)
    cache.set("key1", "value", ttl=1)
    time.sleep(1.5)
    assert cache.get("key1") is None


def test_clear(tmp_path: Path) -> None:
    cache = ResponseCache(path=tmp_path / "cache", default_ttl=60)
    cache.set("key1", "v1")
    cache.set("key2", "v2")
    cache.clear()
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_make_key_deterministic(tmp_path: Path) -> None:
    cache = ResponseCache(path=tmp_path / "cache", default_ttl=60)
    k1 = cache.make_key(["url1", "url2"], "prompt", "gemini", "rich")
    k2 = cache.make_key(["url1", "url2"], "prompt", "gemini", "rich")
    k3 = cache.make_key(["url1", "url2"], "prompt", "gemini", "poor")
    assert k1 == k2
    assert k1 != k3


def test_make_key_order_independent(tmp_path: Path) -> None:
    cache = ResponseCache(path=tmp_path / "cache", default_ttl=60)
    k1 = cache.make_key(["a", "b"], "p", "gemini", "poor")
    k2 = cache.make_key(["b", "a"], "p", "gemini", "poor")
    assert k1 == k2
