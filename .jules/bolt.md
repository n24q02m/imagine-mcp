## 2026-05-20 - SSRF Custom Client and Local Imports
**Context:** During code review for Grok provider, the reviewer incorrectly noted that `get_ssrf_safe_client` was undefined and not imported.
**Learning:** `get_ssrf_safe_client` is actually correctly imported inside the `generate_image` and `generate_video` functions via local imports (`from imagine_mcp.media import get_ssrf_safe_client`) which was implemented this way to avoid circular imports. This code runs perfectly fine and tests passed.
**Verification:** We used `grep -n "get_ssrf_safe_client" src/imagine_mcp/providers/grok.py` to prove that the function is indeed defined and imported properly.
