---
name: Bug report
about: Create a report to help us improve
title: ''
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:

1. Go to '...'
2. Call tool '....'
3. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Tool call**
If applicable, share the exact `understand` / `generate` / `config` / `help` call (scrub any API keys):

```json
{
  "tool": "generate",
  "args": {
    "media_type": "image",
    "prompt": "...",
    "provider": "gemini",
    "tier": "rich"
  }
}
```

**Environment (please complete the following information):**

- OS: [e.g. macOS, Linux, Windows]
- Python version: [e.g. 3.13]
- Package version: [e.g. 1.0.0]
- Installation method: [e.g. uvx, pip, Docker]
- Provider(s) affected: [e.g. gemini, openai, grok]

**Additional context**
Add any other context about the problem here.
