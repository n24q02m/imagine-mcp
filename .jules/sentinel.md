## 2025-06-23 - [HIGH] Unbounded download streams leading to DoS
**Vulnerability:** Downloader allowed writing chunks to disk even if the total size exceeded the 50MB limit, by only checking the limit *after* writing the chunk. Additionally, it didn't check Content-Length headers early.
**Learning:** Checking limits *after* an operation (like writing to disk) allows for a one-chunk "overread" and doesn't prevent resource consumption if the header already signals an oversized payload.
**Prevention:** Always perform a pre-flight check on Content-Length headers if available, and validate that bytes_read + len(chunk) does not exceed the limit before processing/writing the chunk.
## 2026-06-30 - Missing validation of PUBLIC_URL schema and related parameters
**Vulnerability:** The server lacked rigorous validation for `PUBLIC_URL`, `MCP_HOST`, and `MCP_PORT` when starting in multi-user remote mode. Specifically, `PUBLIC_URL` schema and hostname weren't strictly checked, and `MCP_HOST`/`MCP_PORT` had no validation at all before being used.
**Learning:** Even internal configuration parameters provided via environment variables must be treated as untrusted input in multi-user or remote-accessible scenarios to prevent misconfiguration or potential exploitation (e.g., SSRF via malformed URLs, or port/host hijacking).
**Prevention:** Implement fail-fast validation for all network-related environment variables at startup. Use robust libraries or regex for IP/hostname validation and enforce strict ranges for ports.
