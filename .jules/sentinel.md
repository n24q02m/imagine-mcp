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
## 2026-07-03 - [MEDIUM] Add input validation for MCP_PORT and MCP_HOST
**Vulnerability:** The application blindly casted `MCP_PORT` to an integer and passed `MCP_HOST` without verifying format validity. Malformed environment variables could cause unhandled exceptions leading to stack trace leakage or unexpected behavior.
**Learning:** Application startup code should robustly validate user-provided environment configuration (like port numbers and IPs/hostnames) and handle exceptions securely (using clear log messages or generic exits instead of throwing internal tracebacks).
**Prevention:** Use defensive parsing (`int()` with range checks for ports, `ipaddress.ip_address` or regex for hostnames) and employ `try...except` blocks that catch formatting errors, raising clean `SystemExit` messages using `from None` to hide internal stack traces from operators.
