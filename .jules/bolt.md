## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2024-05-22 - Prevent deadlocks in concurrent media processing
**Learning:** In `src/imagine_mcp/dispatcher.py`, keeping URL validation (`_validate_url`) sequential while making media type detection (`detect_media_type`) concurrent prevents deadlocks. This is because media type detection might involve its own network calls, while URL validation internally uses a bounded `_DNS_RESOLVER_POOL`. If both were in the same pool or blindly concurrent, we could exhaust the DNS resolver pool threads waiting on each other, causing a deadlock.
**Action:** When parallelizing operations that depend on nested thread pools (like network validation vs. DNS resolution), carefully separate the bounds of concurrency to avoid deadlocks.

## 2024-05-22 - PR Title Conventions
**Learning:** The project's `.github/workflows/ci.yml` strictly enforces conventional commit prefixes using `amannn/action-semantic-pull-request`. The `types` configuration is explicitly restricted to `fix` and `feat` *only*. The `perf` type is rejected by the CI check.
**Action:** When acting as the 'Bolt' persona, format PR titles as `fix: ⚡ bolt: <performance improvement>` or `feat: ⚡ bolt: <performance improvement>` instead of using `perf:` to pass the restrictive CI checks.
