## 2025-06-23 - [HIGH] Unbounded download streams leading to DoS
**Vulnerability:** Downloader allowed writing chunks to disk even if the total size exceeded the 50MB limit, by only checking the limit *after* writing the chunk. Additionally, it didn't check Content-Length headers early.
**Learning:** Checking limits *after* an operation (like writing to disk) allows for a one-chunk "overread" and doesn't prevent resource consumption if the header already signals an oversized payload.
**Prevention:** Always perform a pre-flight check on Content-Length headers if available, and validate that bytes_read + len(chunk) does not exceed the limit before processing/writing the chunk.

## 2025-06-25 - [HIGH] Unbounded read size in leaderboard fetcher
**Vulnerability:** The leaderboard fetch script used `iter_text()` and accumulated chunks without a pre-flight `Content-Length` check, and only checked the size *after* incrementing a counter, potentially allowing memory exhaustion DoS.
**Learning:** Even internal-use scripts that fetch data from external sources must follow strict download safety patterns (pre-flight checks and check-before-append).
**Prevention:** Use `iter_bytes()` for precise byte counting, perform pre-flight `Content-Length` checks, and always validate the predicted total size (`bytes_read + len(chunk)`) against the limit *before* adding data to in-memory buffers.
