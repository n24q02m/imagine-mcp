## 2026-05-06 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2026-05-25 - Optimize redundant network I/O in Gemini multi-URL processing
**Learning:** In the `understand_multimodal` function of the Gemini provider, calculating `detect_media_type` for every URL redundantly duplicated the work already concurrently performed by `dispatch_understand` in the dispatcher. This led to O(N) sequential HTTP HEAD requests, creating a performance bottleneck for multi-URL prompts. By passing the pre-calculated `media_types` array from the dispatcher down to the provider, we converted this O(N) penalty into an O(1) bounded operation.
**Action:** When a dispatcher or upstream caller computes expensive metadata (like media types) to make routing decisions, pass that pre-calculated data down to the provider to avoid duplicating expensive network requests.

## 2026-05-25 - Optimize environment variable iteration
**Learning:** `credentials_for_current_request` iteratively read over `os.environ.items()`, which scales with the total number of environment variables O(N). Because we only need `CLOUD_KEYS`, which is bounded, we can retrieve them directly `os.environ.get(k)`, making it O(1).
**Action:** When extracting a subset of known keys from a large dict or environment, iterate over the known keys rather than filtering the entire mapping.

## 2026-05-28 - Request-Scoped ContextVar Caching for I/O Heavy Credentials
**Learning:** In a multi-user HTTP architecture where credentials are encrypted and stored per user (sub), resolving credentials via `PerPluginStore.load()` triggered expensive file reads, AES-GCM decryption, and JSON parsing on *every* API lookup (e.g. `_default_provider`, `_api_key`). Caching this lookup on a per-request basis using `contextvars.ContextVar` eliminates these redundant operations. However, because `ContextVar` instances inherit state in sequentially executed asyncio test tasks (running in the same OS thread), the cache must be explicitly reset using an `autouse=True` fixture in `conftest.py` to prevent state leakage and isolated test failures.
**Action:** Use `contextvars.ContextVar` for request-scoped caching to eliminate redundant disk/crypto operations per API request. When doing so, always ensure test suites have an `autouse` fixture to manually reset the contextvar to maintain test isolation.

## 2026-06-11 - Optimize media fetching concurrency in understand flows
**Learning:** Sequential network I/O in async loops like `for u in urls: await fetch(u)` bounds performance to O(N) latency. By extracting loop bodies into async helper functions and awaiting them via `asyncio.gather`, we reduce latency to O(1). When doing this with operations that generate temporary resources (e.g. downloads), ensure cleanup paths are registered *before* an `await` within the gathered task (e.g., append `tmp_path` to tracking list before awaiting download) to prevent resource leaks in partial failure scenarios.
**Action:** Replace sequential `await` loops with `asyncio.gather(*(_helper() for item in list))` to execute async I/O concurrently, while carefully managing temporary file cleanup ordering inside the gathered tasks.

## 2026-06-13 - Optimize URL processing with native Async I/O
**Learning:** The previous recommendation to use `ThreadPoolExecutor.map` for media detection was suboptimal and synchronous across the pool. Native `asyncio.gather` provides better performance and integration. Additionally, sequential URL validation was an O(N) bottleneck; parallelizing it is safe as `validate_url_and_get_ip` offloads to a dedicated `_DNS_RESOLVER_POOL`, avoiding deadlocks.
**Action:** Use native `asyncio` concurrency for URL validation and metadata detection rather than delegating to a thread pool.

## 2026-06-13 - Request-Scoped ContextVar Caching for Sub-Aware Configurations
**Learning:** `config_value_for_current_request` in `src/imagine_mcp/credential_state.py` retrieved configurations directly via `read_for_sub(sub)` for every lookup (like `UNDERSTAND_MODELS` and `GENERATE_MODELS` chained across requests). Since `read_for_sub` invokes `PerPluginStore.load()` internally, this introduced redundant disk I/O, JSON parsing, and AES-GCM decryption for *each* configuration variable requested during a single tool call. Even though credentials were being cached via the `_request_creds` `ContextVar`, the configuration lookups were incorrectly bypassing that cache.
**Action:** Always route configuration variable lookups through the same request-scoped cache used for credentials when operating under the same tenant isolation boundaries, avoiding repetitive and expensive I/O operations per key.

## 2026-06-15 - Optimize thread-safe lazy initialization
**Learning:** In a highly concurrent asynchronous environment, simple global `if _CLIENT is None:` checks can lead to a race condition where multiple expensive `httpx.Client` or `httpx.AsyncClient` instances are instantiated simultaneously by different tasks. This causes connection pool memory leaks and redundant instantiation overhead.
**Action:** Use a thread-safe `_ClientManager` class with `threading.Lock` and the double-checked locking pattern to ensure singletons are truly instantiated only once, preserving memory and improving efficiency under load.

## 2026-06-21 - Optimize file download chunking
**Learning:** Native `anyio.open_file` is much faster for writing small chunks inside an async iteration compared to `await asyncio.to_thread(f.write, chunk)`. Using `to_thread` repeatedly within a loop introduces significant context-switching overhead.
**Action:** Always prefer native asynchronous file I/O operations (like `anyio`) for fine-grained chunked streaming in high-frequency loops instead of delegating individual chunk writes to thread pools.

## 2026-06-29 - [TEST] Mocking threaded DNS resolution in dispatcher
**Learning:** The `_validate_url` function in `src/imagine_mcp/dispatcher.py` wraps the blocking `validate_url_and_get_ip` call using `asyncio.to_thread`. To test this without triggering real DNS resolution or hitting sandbox network limits, `monkeypatch` can be used to swap the internal `validate_url_and_get_ip` reference with a synchronous mock. This ensures the test remains fast and deterministic while still verifying that the dispatcher correctly awaits the threaded work and propagates exceptions.
**Action:** Use `monkeypatch.setattr` to mock blocking functions wrapped in `asyncio.to_thread` when writing unit tests for async dispatchers.

## 2026-06-30 - [TEST] Achieve 100% coverage for dispatcher validation logic
**Learning:** Achieved 100% test coverage for `src/imagine_mcp/dispatcher.py` by targeting previously untested edge cases in `asyncio.gather` error propagation and configuration-driven provider selection. Mocking internal async utilities like `detect_media_type_async` and `_validate_url` (which wraps threaded blocking I/O) allows for robust unit testing of high-level dispatch logic without actual network dependencies.
**Action:** When extending test coverage for dispatchers, use a dedicated extension test file to isolate new edge cases and mock all internal network-bound helpers to ensure test suite stability and speed.

## 2026-07-10 - Consolidate consecutive synchronous I/O in async contexts
**Learning:** Executing consecutive synchronous file operations (e.g., `mkdir` followed by `write_bytes`) by wrapping each individually in `asyncio.to_thread` introduces unnecessary thread-pool scheduling and context-switching overhead.
**Action:** When performing multiple related blocking operations in an async context, consolidate them into a single synchronous helper function and execute that helper via a single `asyncio.to_thread()` call.

## 2026-07-25 - Pipeline a fast async phase into the slow phase with TaskGroup
**Learning:** Splitting "resolve metadata" and "fetch content" into two sequential `asyncio.gather` calls imposes a barrier: no item may start fetching until the slowest probe of *every* item has finished, costing `max(probe) + max(fetch)` where per-item pipelining costs `max(probe + fetch)`. This barrier is never faster and is often slower. An earlier entry rejected pipelining because it would lose fail-fast behaviour, but that objection only applies to collapsing the phases into one `gather(return_exceptions=True)`, which cannot cancel anything -- that form already defeated fail-fast, since it ran every task to completion before raising the first error. `asyncio.TaskGroup` pipelines *and* cancels the remaining tasks on the first failure, so it is strictly better on both axes. Landed in `dispatcher.py` (b9071ea) and `providers/gemini.py` (this entry); both call sites are now done.
**Action:** When a fast async phase feeds a slow one, put both in a single per-item helper and run the helpers under `asyncio.TaskGroup`. Read results back by index so output stays in input order, unwrap the `ExceptionGroup` so callers still see the concrete error type, and register any cleanup (e.g. appending a temp path) *before* the first `await` inside the helper so a cancelled task is still cleaned up.

## Rejected

Proposals evaluated and turned down. The reasoning lives here so it carries to the next run.

- **2026-07-02 - "preserve the barrier between validation and fetch" (superseded).** This entry told future runs *not* to pipeline. It was wrong on the facts: it defended a fail-fast property that `gather(return_exceptions=True)` did not actually provide, and it named only `gather`, which left `TaskGroup` open as a loophole. Between 2026-07-02 and 2026-07-25 it produced five duplicate PRs against the same function (#481, #482, #484, #488, #491), each re-proposing the pipeline with `TaskGroup` to route around the wording. Replaced by the 2026-07-25 entry above. When an approach is genuinely off-limits, say what to do instead; a bare prohibition just gets worked around.
- **`perf:` as a commit or PR title prefix.** This repo enforces a `fix:`/`feat:` subset, and the "Validate PR title" check fails the PR outright. A performance change is a `fix:`. Five PRs in the cluster above were opened with `perf:` and all five failed that check before review.
- **Persona markers in source comments.** Comments of the form `# ⚡ Bolt: ... Expected impact: ...` were removed from `credential_state.py`, `dispatcher.py`, `media.py` and `providers/gemini.py`. This is a public repository; a comment should describe the code, not who wrote it or how much it was expected to help. Write the rationale, drop the tag.
- **A PR that changes nothing.** #482 ("evaluated performance optimizations", empty diff) and #485 (palette persona, empty diff) carried no changes. If a run finds no work, record it here and stop -- do not open an empty PR.
## 2026-08-01 - Consolidate multiple system fetches into a single sync helper for asyncio.to_thread
**Learning:** The `config(action="status")` handler dispatched `asyncio.to_thread` three separate times to fetch the server version, evaluate credentials state, and query the live store. While these calls are unblocked, sequentially awaiting `asyncio.to_thread` three times in one function incurs unnecessary thread-pool scheduling overhead and context switching.
**Action:** When a block of code requires multiple synchronous (and especially I/O bound or configuration reading) functions, wrap them in a single synchronous helper (like `_get_system_status_sync`) and execute that helper via a single `asyncio.to_thread()` call to minimize overhead.
