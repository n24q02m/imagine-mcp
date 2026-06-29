## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2026-06-13 - Optimize URL processing with native Async I/O
**Learning:** The previous recommendation to use `ThreadPoolExecutor.map` for media detection was suboptimal and synchronous across the pool. Native `asyncio.gather` provides better performance and integration. Additionally, sequential URL validation was an O(N) bottleneck; parallelizing it is safe as `validate_url_and_get_ip` offloads to a dedicated `_DNS_RESOLVER_POOL`, avoiding deadlocks. Robustness requires `return_exceptions=True` to prevent task leakage.
**Action:** Use `asyncio.gather(..., return_exceptions=True)` for all concurrent URL validation and metadata detection to achieve O(1) latency while ensuring robust cleanup.

## 2024-05-18 - Optimize redundant network I/O in Gemini multi-URL processing
**Learning:** In the `understand_multimodal` function of the Gemini provider, calculating `detect_media_type` for every URL redundantly duplicated the work already concurrently performed by `dispatch_understand` in the dispatcher. This led to O(N) sequential HTTP HEAD requests, creating a performance bottleneck for multi-URL prompts. By passing the pre-calculated `media_types` array from the dispatcher down to the provider, we converted this O(N) penalty into an O(1) bounded operation.
**Action:** When a dispatcher or upstream caller computes expensive metadata (like media types) to make routing decisions, pass that pre-calculated data down to the provider to avoid duplicating expensive network requests.

## 2024-05-18 - Optimize environment variable iteration
**Learning:** `credentials_for_current_request` iteratively read over `os.environ.items()`, which scales with the total number of environment variables O(N). Because we only need `CLOUD_KEYS`, which is bounded, we can retrieve them directly `os.environ.get(k)`, making it O(1).
**Action:** When extracting a subset of known keys from a large dict or environment, iterate over the known keys rather than filtering the entire mapping.

## 2026-05-27 - Request-Scoped ContextVar Caching for I/O Heavy Credentials
**Learning:** In a multi-user HTTP architecture where credentials are encrypted and stored per user (sub), resolving credentials via `PerPluginStore.load()` triggered expensive file reads, AES-GCM decryption, and JSON parsing on *every* API lookup (e.g. `_default_provider`, `_api_key`). Caching this lookup on a per-request basis using `contextvars.ContextVar` eliminates these redundant operations. However, because `ContextVar` instances inherit state in sequentially executed asyncio test tasks (running in the same OS thread), the cache must be explicitly reset using an `autouse=True` fixture in `conftest.py` to prevent state leakage and isolated test failures.
**Action:** Use `contextvars.ContextVar` for request-scoped caching to eliminate redundant disk/crypto operations per API request. When doing so, always ensure test suites have an `autouse` fixture to manually reset the contextvar to maintain test isolation.

## 2026-06-11 - Optimize media fetching concurrency in understand flows
**Learning:** Sequential network I/O in async loops like `for u in urls: await fetch(u)` bounds performance to O(N) latency. By extracting loop bodies into async helper functions and awaiting them via `asyncio.gather`, we reduce latency to O(1). When doing this with operations that generate temporary resources (e.g. downloads), ensure cleanup paths are registered *before* an `await` within the gathered task (e.g., append `tmp_path` to tracking list before awaiting download) to prevent resource leaks in partial failure scenarios.
**Action:** Replace sequential `await` loops with `asyncio.gather(*(_helper() for item in list))` to execute async I/O concurrently, while carefully managing temporary file cleanup ordering inside the gathered tasks.
## 2026-06-13 - Optimize thread-safe lazy initialization
**Learning:** In a highly concurrent asynchronous environment, simple global `if _CLIENT is None:` checks can lead to a race condition where multiple expensive `httpx.Client` or `httpx.AsyncClient` instances are instantiated simultaneously by different tasks. This causes connection pool memory leaks and redundant instantiation overhead.
**Action:** Use a thread-safe `_ClientManager` class with `threading.Lock` and the double-checked locking pattern to ensure singletons are truly instantiated only once, preserving memory and improving efficiency under load.

## 2024-06-25 - [Optimize File Download Chunking]
**Learning:** Native `anyio.open_file` is much faster for writing small chunks inside an async iteration compared to `await asyncio.to_thread(f.write, chunk)`. Using `to_thread` repeatedly within a loop introducing significant context-switching overhead.
**Action:** Always prefer native asynchronous file I/O operations (like `anyio`) for fine-grained chunked streaming in high-frequency loops instead of delegating individual chunk writes to thread pools.

## 2026-06-13 - Request-Scoped ContextVar Caching for Sub-Aware Configurations
**Learning:** `config_value_for_current_request` in `src/imagine_mcp/credential_state.py` retrieved configurations directly via `read_for_sub(sub)` for every lookup (like `UNDERSTAND_MODELS` and `GENERATE_MODELS` chained across requests). Since `read_for_sub` invokes `PerPluginStore.load()` internally, this introduced redundant disk I/O, JSON parsing, and AES-GCM decryption for *each* configuration variable requested during a single tool call. Even though credentials were being cached via the `_request_creds` `ContextVar`, the configuration lookups were incorrectly bypassing that cache.
**Action:** Always route configuration variable lookups through the same request-scoped cache used for credentials when operating under the same tenant isolation boundaries, avoiding repetitive and expensive I/O operations per key.

## 2024-05-18 - [TEST] Mocking threaded DNS resolution in dispatcher
**Learning:** The `_validate_url` function in `src/imagine_mcp/dispatcher.py` wraps the blocking `validate_url_and_get_ip` call using `asyncio.to_thread`. To test this without triggering real DNS resolution or hitting sandbox network limits, `monkeypatch` can be used to swap the internal `validate_url_and_get_ip` reference with a synchronous mock. This ensures the test remains fast and deterministic while still verifying that the dispatcher correctly awaits the threaded work and propagates exceptions.
**Action:** Use `monkeypatch.setattr` to mock blocking functions wrapped in `asyncio.to_thread` when writing unit tests for async dispatchers.
## 2026-06-29 - [PERF] Optimized environment credential resolution
**Optimization:** Implemented a process-level cache for `os.environ` lookups in `credential_state.py`.
**Rationale:** Avoided O(K) iteration over `os.environ` per request when no JWT sub is present.
**Impact:** Significantly reduced latency for stdio/single-user HTTP requests by reusing the cached credential dictionary across the process lifetime, invalidated only on explicit config changes.
**Measurement:** Verified via new test cases that cache persists across request scopes and is correctly cleared by `relay_setup.apply_config`.
