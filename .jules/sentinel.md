## 2026-06-29 - [HIGH] Unbounded download streams leading to DoS
**Vulnerability:** Downloader allowed writing chunks to disk even if the total size exceeded the 50MB limit, by only checking the limit *after* writing the chunk. Additionally, it didn't check Content-Length headers early.
**Learning:** Checking limits *after* an operation (like writing to disk) allows for a one-chunk "overread" and doesn't prevent resource consumption if the header already signals an oversized payload.
**Prevention:** Always perform a pre-flight check on Content-Length headers if available, and validate that bytes_read + len(chunk) does not exceed the limit before processing/writing the chunk.

## 2026-06-30 - [HIGH] Unbounded read size in leaderboard fetcher
**Vulnerability:** The leaderboard fetch script used `iter_text()` and accumulated chunks without a pre-flight `Content-Length` check, and only checked the size *after* incrementing a counter, potentially allowing memory exhaustion DoS.
**Learning:** Even internal-use scripts that fetch data from external sources must follow strict download safety patterns (pre-flight checks and check-before-append).
**Prevention:** Use `iter_bytes()` for precise byte counting, perform pre-flight `Content-Length` checks, and always validate the predicted total size (`bytes_read + len(chunk)`) against the limit *before* adding data to in-memory buffers.

## 2026-06-30 - [LOW] Unsafe os.path.splitext() in URL handling
**Vulnerability:** Use of `os.path.splitext()` for URL extensions is platform-dependent and susceptible to bypasses if query parameters or fragments are not perfectly stripped.
**Learning:** `os.path.splitext()` follows the host OS's path rules (e.g., handling backslashes on Windows), which may not align with URL path semantics. Also, manual string splitting for URL components is error-prone compared to standard `urlparse`.
**Prevention:** Use `urllib.parse.urlparse` to extract the path from a URL, and use `posixpath.splitext()` to ensure consistent extension extraction regardless of the server's operating system.

## 2026-07-05 - [MEDIUM] Add input validation for MCP_PORT and MCP_HOST
**Vulnerability:** The application blindly casted `MCP_PORT` to an integer and passed `MCP_HOST` without verifying format validity. Malformed environment variables could cause unhandled exceptions leading to stack trace leakage or unexpected behavior.
**Learning:** Application startup code should robustly validate user-provided environment configuration (like port numbers and IPs/hostnames) and handle exceptions securely (using clear log messages or generic exits instead of throwing internal tracebacks).
**Prevention:** Use defensive parsing (`int()` with range checks for ports, `ipaddress.ip_address` or regex for hostnames) and employ `try...except` blocks that catch formatting errors, raising clean `SystemExit` messages using `from None` to hide internal stack traces from operators.

## 2026-07-17 - [Path Obfuscation Auth Bypass]
**Vulnerability:** Edge authentication gate in src/worker.ts bypassed using obfuscated URLs (e.g., //mcp or /%2Fmcp).
**Learning:** Checking strict path strings against unnormalized request paths allows attackers to evade authentication checks before hitting internal endpoints.
**Prevention:** Always decode and normalize URIs (using decodeURIComponent and replace) before conducting path-based security or routing decisions, and correctly handle malformed URIs.

## 2026-07-25 - [LOW] Exception detail returned to the caller from reset_credentials
**Vulnerability:** `reset_credentials` in `src/imagine_mcp/relay_setup.py` returned `str(exc)` in its result dict. `server.py` hands that dict back unchanged as the `config` tool result, so an `OSError` from `PerPluginStore` (for example `PermissionError: [Errno 13] Permission denied: '/srv/.../config.enc'`) put the server-side store path in front of the caller. Reachable in multi-user HTTP mode, where the caller is not the operator.
**Learning:** The boundary that matters is not "is this an HTTP handler" but "does this value reach the caller". A plain dict returned from a tool implementation is a response body.
**Prevention:** Log the exception, return a fixed message. When auditing, trace the return value to its call site to confirm it crosses the boundary, and check which exception types the `try` block can actually raise -- the leak is only as bad as what those messages carry.

## Rejected

Proposals evaluated and turned down. The reasoning lives here so it carries to the next run.

- **Replacing this file's history with a single entry (#492).** The PR that reported the `reset_credentials` leak also deleted every prior entry in this ledger, leaving only its own. The finding was correct and has been implemented (see the 2026-07-25 entry), but this file is the record of what has already been fixed; clearing it makes past work invisible to the next run and invites re-proposal of things already landed. Append, never rewrite. #489 reported the same issue and appended correctly.
- **Asserting on the exact error string.** The test proposed alongside #492 asserted `result["error"] == "Internal server error"`, which pins the wording rather than the property. The committed test asserts that the store path and `Errno` do *not* appear in the response, which is what actually matters and survives a reword.

## 2026-08-11 - [CRITICAL] Prevent environment variable injection in relay config
**Vulnerability:** The relay configuration processing in `apply_config` took user-submitted payload keys and updated `os.environ` without validating against an allowed set, potentially allowing attackers to overwrite critical environment variables (e.g., path settings or internal API secrets).
**Learning:** Any endpoint or mechanism that accepts configuration data from external sources and applies it to the environment must strictly filter the incoming keys against an allowlist.
**Prevention:** Introduce and enforce an `ALLOWED_CONFIG_KEYS` check before applying any key-value pair to `os.environ`.
