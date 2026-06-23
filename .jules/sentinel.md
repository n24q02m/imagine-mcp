## 2025-06-23 - Robust Extension Extraction
**Vulnerability:** Use of unsafe os.path.splitext() which could be vulnerable to bypass or unexpected results with malicious inputs.
**Learning:** Standard library functions like os.path.splitext() are useful but may not enforce strict enough constraints for security-sensitive operations. Validating the output against a strict allowlist (e.g., alphanumeric, length-limited) is essential.
**Prevention:** Always validate file extensions against a strict regex or character set (isalnum) and enforce reasonable length limits.
