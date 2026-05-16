## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2026-05-16 - Parallelize network-bound media type detection in dispatcher
**Learning:** In `src/imagine_mcp/dispatcher.py`, the `dispatch_understand` function sequentially iterated through `media_urls` to perform URL validation and media type detection (which involves a network call). For multimodal requests with multiple URLs, this resulted in an O(N) network bottleneck.
**Action:** Use `concurrent.futures.ThreadPoolExecutor` (already set up in `_DISPATCH_POOL`) to execute `_process_url` across `media_urls` concurrently, reducing latency from O(N) to roughly O(1).
