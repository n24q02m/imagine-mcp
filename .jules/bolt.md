## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2024-05-18 - Optimize media type detection concurrency
**Learning:** `detect_media_type` in `dispatch_understand` involves sequential network requests per media URL, resulting in O(N) latency. By replacing the list comprehension with `_DISPATCH_POOL.map` (using a `ThreadPoolExecutor`), we can reduce latency to O(1) bounded by max_workers. Wrapping `map` in `list()` is critical to evaluate the generator immediately and preserve fail-fast error handling. We also need to keep URL validation sequential to prevent deadlocks with nested thread pools (like `_DNS_RESOLVER_POOL`).
**Action:** Use `ThreadPoolExecutor.map` wrapped in `list()` to efficiently resolve concurrent I/O operations and carefully manage nested thread pools to avoid deadlocks.
