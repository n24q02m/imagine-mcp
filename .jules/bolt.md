## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2024-05-18 - Concurrent network calls in dispatch_understand
**Learning:** `dispatch_understand` processed `media_urls` sequentially, meaning 3 remote URLs took 3x the latency to determine their media type. `ThreadPoolExecutor` effectively parallelizes these network-bound HTTP HEAD checks.
**Action:** Use `concurrent.futures.ThreadPoolExecutor.map()` to run independent network operations in parallel. Wrap the result generator in `list()` to evaluate immediately and raise the first encountered exception, avoiding unexpected lazy evaluation behavior down the stack.
