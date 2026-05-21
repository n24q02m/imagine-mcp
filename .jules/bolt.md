## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2024-05-21 - Concurrent media type detection in dispatcher
**Learning:** In `dispatch_understand`, detecting media types sequentially for `media_urls` introduces O(N) network latency. Using a thread pool (`ThreadPoolExecutor`) to evaluate the URLs concurrently reduces latency to ~O(1) concurrent latency. Wrapping the generator returned by `ThreadPoolExecutor.map` in a `list()` ensures immediate evaluation and fail-fast behavior if any URL check raises an exception.
**Action:** Use concurrent fetching for repetitive network operations across items (e.g. HEAD requests on multiple URLs) instead of sequential loops.
