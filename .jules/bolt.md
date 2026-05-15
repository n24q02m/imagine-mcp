## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2024-05-19 - Parallelize batch network I/O in dispatcher
**Learning:** `dispatch_understand` handles batches of URLs sequentially for validation and type detection (`HEAD` requests). This causes O(N) latency growth for multimodal prompts (e.g., Gemini).
**Action:** Use a module-level `ThreadPoolExecutor.map` to parallelize high-latency network checks for URL lists, effectively making latency O(1) bounded by the slowest response, while using `list()` to maintain immediate error propagation. Moreover, pre-computed properties should be passed down to downstream functions to avoid redundant network I/O.
