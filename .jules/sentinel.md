## 2026-06-23 - [SECURITY] Incomplete validation of MCP_HOST configuration
**Vulnerability:** The `MCP_HOST` and `MCP_PORT` environment variables were used without validation, which could allow starting the server with invalid or malicious configurations in multi-user remote mode.
**Learning:** Always validate external configuration inputs (like environment variables) before they are used to bind a network service.
**Prevention:** Use the `ipaddress` module and regex for hostname validation to ensure the host is a valid IP or hostname, and verify the port range.
