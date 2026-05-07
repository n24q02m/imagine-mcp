## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.
## 2026-05-07 - Parallelize media type detection in dispatch_understand
**Learning:** Sequential `detect_media_type` calls for multiple URLs in `dispatch_understand` created an N+1 network bottleneck. Parallelizing these calls using a `ThreadPoolExecutor` reduces latency from O(N) to O(1) (relative to the slowest request) for small batches of URLs.
**Action:** Use `ThreadPoolExecutor` to concurrently perform independent network-bound validation and detection tasks for collections of user-provided URLs.
