## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.
## 2026-05-07 - Avoid redundant media type detection in Gemini multimodal
**Learning:** `dispatch_understand` in `dispatcher.py` already computes media types for all URLs. Passing these pre-computed types to the provider's `understand_multimodal` function avoids redundant synchronous network calls (HEAD requests) for each URL in Gemini's multimodal path, improving latency and reducing outgoing requests.
**Action:** Pass pre-computed media metadata from dispatchers to providers whenever possible to avoid duplicate IO-bound detection logic.
