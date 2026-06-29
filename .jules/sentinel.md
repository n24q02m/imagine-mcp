## 2025-06-23 - [HIGH] Unbounded download streams leading to DoS
**Vulnerability:** Downloader allowed writing chunks to disk even if the total size exceeded the 50MB limit, by only checking the limit *after* writing the chunk. Additionally, it didn't check Content-Length headers early.
**Learning:** Checking limits *after* an operation (like writing to disk) allows for a one-chunk "overread" and doesn't prevent resource consumption if the header already signals an oversized payload.
**Prevention:** Always perform a pre-flight check on Content-Length headers if available, and validate that bytes_read + len(chunk) does not exceed the limit before processing/writing the chunk.

## 2026-06-29 - [SECURITY] Incomplete validation of MCP_HOST configuration
**Vulnerability:** Incomplete validation of `MCP_HOST` and `MCP_PORT` environment variables when running in remote relay mode allowed potentially dangerous or invalid configurations to be passed to the underlying server transport.
**Learning:** Network listener configurations (host/port) derived from environment variables must be strictly validated against expected ranges and formats (e.g., `ipaddress` validation for IPs and regex for hostnames) to prevent startup crashes or binding to unintended interfaces.
**Prevention:** Implement fail-fast validation for all network-related configuration variables at application startup, using `SystemExit` to prevent execution with invalid parameters.
