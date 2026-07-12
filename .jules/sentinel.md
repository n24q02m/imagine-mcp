## 2025-02-14 - Edge Auth Gate Path Obfuscation Bypass
**Vulnerability:** The Cloudflare worker edge auth gate in `src/worker.ts` checked `url.pathname === '/mcp'` directly. This could be bypassed by a client sending requests to `//mcp` or URI-encoded variations like `/%6dcp`, preventing the fast-fail structural check from firing.
**Learning:** Cloudflare Workers `URL.pathname` properties preserve some raw formatting variations (like multiple leading slashes) which can subvert naive string matching in edge routing logic.
**Prevention:** Always decode and normalize (e.g., `decodeURIComponent(url.pathname).replace(/^\/+/, '/')` wrapped in a `try/catch`) request paths at the edge before evaluating auth or routing conditions.
