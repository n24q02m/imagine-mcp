## 2026-06-13 - [Unsafe Bind Address]
**Vulnerability:** The server used a hardcoded 0.0.0.0 bind address in the Dockerfile and (historically) in the server code, exposing it to the entire network when not behind a proxy.
**Learning:** Hardcoding 0.0.0.0 is a common convenience that bypasses local binding restrictions but introduces significant risk in production environments without proper networking controls.
**Prevention:** Always default to 127.0.0.1 for server bindings. Require explicit opt-in for 0.0.0.0 through environment variables or configuration files, and ensure that security-sensitive configurations are regularly audited.
