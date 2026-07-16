# Security Policy

## Supported Versions

The latest stable release is supported. Older versions receive no security patches.

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, report via GitHub Security Advisories:

1. Go to https://github.com/n24q02m/imagine-mcp/security/advisories/new
2. Fill out the advisory form.
3. You will receive a response within 7 days.

## Scope

In scope:

- Credential leakage in error messages, logs, or telemetry
- SSRF / path traversal in `media_urls` or `reference_image_url` parameters
- Prompt injection bypassing the `<untrusted_user_content>` XML boundary
- Supply chain attacks on pinned dependencies (reported via Renovate or GitHub security)

Out of scope:

- Upstream provider vulnerabilities (report to Google / OpenAI / xAI)
- Relay session hijacking or ECDH implementation flaws (report to `mcp-core` instead if relay primitive bug)
- Rate limit bypass (not a security boundary — rate limits are provider-side)

## Response process

1. Triage within 7 days.
2. CVE reserved if required.
3. Fix developed in private fork.
4. Coordinated disclosure with reporter.
5. Public advisory + patched release on the same day.
