## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2024-05-18 - Concurrent network I/O in detect_media_type
**Learning:** In `dispatch_understand`, media types for multiple URLs were being detected sequentially using a list comprehension (`[detect_media_type(u) for u in media_urls]`). Since `detect_media_type` makes HTTP HEAD requests when the file extension is missing, this sequential approach created a significant O(N) performance bottleneck.
**Action:** Use a `ThreadPoolExecutor` (like `_DISPATCH_POOL`) and its `map` function to concurrently detect media types, effectively reducing the latency from O(N) to O(1) for network-bound tasks. Wrapping the mapped generator in a `list()` ensures immediate evaluation for fail-fast error handling.
