## 2026-05-20 - [PERF] Repeated iteration over os.environ inside loop

**Optimization:** Implemented a process-level cache for environment credentials in `credential_state.py`.
**Rationale:** `credentials_for_current_request` was performing a dictionary comprehension over `os.environ` on every request when no JWT sub was active. While already O(K) where K is the number of cloud keys, this still incurred the overhead of `os.environ.get` lookups repeatedly.
**Impact:** Reduced credential resolution to O(1) after the first request in a process lifetime.
**Measurement:** Added `tests/test_perf_env_scan.py` which mocks `os.environ.get` and verifies that it is called 0 times on subsequent requests after the initial population.
