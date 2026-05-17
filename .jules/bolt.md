## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.
## 2024-05-18 - Optimize media type detection in dispatch_understand
**Learning:** `detect_media_type` might perform synchronous HTTP HEAD requests to figure out the content type if the file extension isn't in its known list. When processing multiple `media_urls` in `dispatch_understand`, sequential execution creates a significant performance bottleneck.
**Action:** Use `ThreadPoolExecutor.map` wrapped in `list()` to parallelize network-bound operations over collections, ensuring the generator is fully evaluated to maintain fail-fast error handling.
