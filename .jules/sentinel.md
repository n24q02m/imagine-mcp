## 2025-06-23 - [HIGH] Unbounded download streams leading to DoS
**Vulnerability:** Downloader allowed writing chunks to disk even if the total size exceeded the 50MB limit, by only checking the limit *after* writing the chunk. Additionally, it didn't check Content-Length headers early.
**Learning:** Checking limits *after* an operation (like writing to disk) allows for a one-chunk "overread" and doesn't prevent resource consumption if the header already signals an oversized payload.
**Prevention:** Always perform a pre-flight check on Content-Length headers if available, and validate that bytes_read + len(chunk) does not exceed the limit before processing/writing the chunk.

## 2024-06-29 - Validate MCP_PORT and MCP_HOST environment variables on startup
**Vulnerability:** The application was not validating the MCP_PORT and MCP_HOST environment variables properly. MCP_PORT could have been invalid (e.g. out of range, or a non-integer) and MCP_HOST could have been malformed (e.g. "999.999.999.999" IP bypass).
**Learning:** We need to explicitly validate the type and bounds of port configuration values and make sure hosts match IP or hostname definitions to avoid network issues or bypasses later in the connection lifecycle.
**Prevention:** Perform explicit bounds checking (0-65535) and hostname/IP address validation via ipaddress and regex before launching the HTTP service in remote multi-user mode.
