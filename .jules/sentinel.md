## 2025-06-23 - [HIGH] Unbounded download streams leading to DoS
**Vulnerability:** Downloader allowed writing chunks to disk even if the total size exceeded the 50MB limit, by only checking the limit *after* writing the chunk. Additionally, it didn't check Content-Length headers early.
**Learning:** Checking limits *after* an operation (like writing to disk) allows for a one-chunk "overread" and doesn't prevent resource consumption if the header already signals an oversized payload.
**Prevention:** Always perform a pre-flight check on Content-Length headers if available, and validate that bytes_read + len(chunk) does not exceed the limit before processing/writing the chunk.

## 2025-06-25 - [HIGH] Unbounded read size in leaderboard fetcher
**Vulnerability:** The leaderboard fetch script used `iter_text()` and accumulated chunks without a pre-flight `Content-Length` check, and only checked the size *after* incrementing a counter, potentially allowing memory exhaustion DoS.
**Learning:** Even internal-use scripts that fetch data from external sources must follow strict download safety patterns (pre-flight checks and check-before-append).
**Prevention:** Use `iter_bytes()` for precise byte counting, perform pre-flight `Content-Length` checks, and always validate the predicted total size (`bytes_read + len(chunk)`) against the limit *before* adding data to in-memory buffers.
## 2026-06-29 - [LOW] Unsafe os.path.splitext() in URL handling
**Vulnerability:** Use of `os.path.splitext()` for URL extensions is platform-dependent and susceptible to bypasses if query parameters or fragments are not perfectly stripped.
**Learning:** `os.path.splitext()` follows the host OS's path rules (e.g., handling backslashes on Windows), which may not align with URL path semantics. Also, manual string splitting for URL components is error-prone compared to standard `urlparse`.
**Prevention:** Use `urllib.parse.urlparse` to extract the path from a URL, and use `posixpath.splitext()` to ensure consistent extension extraction regardless of the server's operating system.
## 2026-07-02 - [HIGH] Unvalidated Port and Hostname configuration leading to DoS/SSRF
**Vulnerability:** MCP_PORT and MCP_HOST environment variables were not properly validated before passing them to the underlying HTTP server. An attacker could set MCP_PORT to an invalid value (e.g., 99999) causing an unhandled OverflowError and a server crash (DoS). Furthermore, passing an invalid MCP_HOST could be exploited or bypass validation checks, leading to potential SSRF or unintended listening interfaces.
**Learning:** In public deployments, user-supplied configuration values (even from environment variables) that influence network bindings MUST be strictly validated. The built-in memory instruction already highlighted that MCP_PORT must be an integer (0-65535) and MCP_HOST must be a valid IP or hostname (rejecting malformed IP-like strings).
**Prevention:** Implement strict type and bounds checking for port numbers (0-65535). For hostnames, use `ipaddress.ip_address` to check for valid IPs, and for strings that fail this check but look like IPs (e.g. `999.999.999.999`), reject them immediately before falling back to regex-based hostname validation.
