## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.
- 2026-05-15: Refactored generate functions to use GenerateParams dataclass.
  - Learning: Grouping optional parameters into a dataclass reduces function signature complexity and satisfies linting rules (PLR0913) while maintaining flexibility.
  - Action: Use GenerateParams for all generation-related actions across providers and dispatcher.
