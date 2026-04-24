"""Response cache using diskcache."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import diskcache


class ResponseCache:
    """Wraps diskcache with a deterministic key helper."""

    def __init__(self, path: Path, default_ttl: int = 3600) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self._cache = diskcache.Cache(str(path))
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any:
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._cache.set(key, value, expire=ttl or self._default_ttl)

    def clear(self) -> None:
        self._cache.clear()

    def make_key(
        self, media_urls: list[str], prompt: str, provider: str, tier: str
    ) -> str:
        """Deterministic hash of args for understand cache key."""
        payload = json.dumps(
            {
                "urls": sorted(media_urls),
                "prompt": prompt,
                "provider": provider,
                "tier": tier,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
