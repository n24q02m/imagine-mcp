## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2024-05-18 - Concurrent HTTP requests in map
**Learning:** Python's `ThreadPoolExecutor.map()` is an excellent tool for parallelizing I/O-bound operations (like DNS resolution and HEAD requests) over a list, while perfectly preserving the input order and predictably re-raising the first encountered exception when the iterator is consumed (e.g. by wrapping it in `list()`). This avoids the complexity of manual `submit()` and `as_completed()` loops while matching the exact behavioral contract of sequential execution.
**Action:** Use `list(executor.map(fn, ...))` to easily refactor sequential I/O loops that populate ordered lists or sequences when early exit on exception is still desired.
