## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2024-05-19 - Concurrent Validation and Type Detection in dispatch_understand
**Learning:** `dispatch_understand` processed URL validation (`_validate_url` with DNS lookups) and media type detection (`detect_media_type` with network requests) sequentially, creating an O(N) blocking bottleneck. Using `ThreadPoolExecutor.map()` to process `media_urls` in parallel significantly reduces latency when handling multiple images, while gracefully maintaining fail-fast error behavior by implicitly bubbling up the first encountered error.
**Action:** Always check for repeated network or blocking tasks in `for` loops across multiple inputs. Use a `ThreadPoolExecutor` (max ~16 workers is typically safe for network I/O) to parallelize them.
