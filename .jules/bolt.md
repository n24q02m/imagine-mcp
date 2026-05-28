## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2024-05-18 - Optimize media type detection concurrency
**Learning:** `detect_media_type` in `dispatch_understand` involves sequential network requests per media URL, resulting in O(N) latency. By replacing the list comprehension with `_DISPATCH_POOL.map` (using a `ThreadPoolExecutor`), we can reduce latency to O(1) bounded by max_workers. Wrapping `map` in `list()` is critical to evaluate the generator immediately and preserve fail-fast error handling. We also need to keep URL validation sequential to prevent deadlocks with nested thread pools (like `_DNS_RESOLVER_POOL`).
**Action:** Use `ThreadPoolExecutor.map` wrapped in `list()` to efficiently resolve concurrent I/O operations and carefully manage nested thread pools to avoid deadlocks.

## 2024-05-18 - Optimize redundant network I/O in Gemini multi-URL processing
**Learning:** In the `understand_multimodal` function of the Gemini provider, calculating `detect_media_type` for every URL redundantly duplicated the work already concurrently performed by `dispatch_understand` in the dispatcher. This led to O(N) sequential HTTP HEAD requests, creating a performance bottleneck for multi-URL prompts. By passing the pre-calculated `media_types` array from the dispatcher down to the provider, we converted this O(N) penalty into an O(1) bounded operation.
**Action:** When a dispatcher or upstream caller computes expensive metadata (like media types) to make routing decisions, pass that pre-calculated data down to the provider to avoid duplicating expensive network requests.

## 2024-05-18 - Optimize environment variable iteration
**Learning:** `credentials_for_current_request` iteratively read over `os.environ.items()`, which scales with the total number of environment variables O(N). Because we only need `CLOUD_KEYS`, which is bounded, we can retrieve them directly `os.environ.get(k)`, making it O(1).
**Action:** When extracting a subset of known keys from a large dict or environment, iterate over the known keys rather than filtering the entire mapping.
## 2026-05-27 - Request-Scoped ContextVar Caching for I/O Heavy Credentials
**Learning:** In a multi-user HTTP architecture where credentials are encrypted and stored per user (sub), resolving credentials via `PerPluginStore.load()` triggered expensive file reads, AES-GCM decryption, and JSON parsing on *every* API lookup (e.g. `_default_provider`, `_api_key`). Caching this lookup on a per-request basis using `contextvars.ContextVar` eliminates these redundant operations. However, because `ContextVar` instances inherit state in sequentially executed asyncio test tasks (running in the same OS thread), the cache must be explicitly reset using an `autouse=True` fixture in `conftest.py` to prevent state leakage and isolated test failures.
**Action:** Use `contextvars.ContextVar` for request-scoped caching to eliminate redundant disk/crypto operations per API request. When doing so, always ensure test suites have an `autouse` fixture to manually reset the contextvar to maintain test isolation.

## 2026-05-27 - Optimize media download chunk size
**Learning:** The default chunk size in `httpx` streaming downloads (and many standard implementations) is often 64KB. For high-bandwidth applications fetching large media files (images/videos), this results in a high frequency of syscalls (`read`/`write`) and increased overhead. Increasing the chunk size to 1MB significantly reduces the number of iterations and syscalls, improving throughput and reducing CPU time spent in I/O loops.
**Action:** Use 1MB (1048576 bytes) as the standard chunk size for streaming media downloads to disk to balance memory usage and I/O efficiency.
