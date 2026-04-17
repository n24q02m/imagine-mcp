# imagine-mcp

MCP server for image/video understanding and generation with a 2×2×3 architecture (Action × Tier × Provider).

## Install

```bash
uv sync
doppler run --project virtual-company --config dev -- uv run imagine-mcp
```

## Mega-tool schema

```python
imagine(action, provider, tier, **kwargs)
```

- `action`: `understand` | `generate` | `edit` | `video_status`
- `provider`: `gemini` | `openai` | `grok`
- `tier`: `poor` | `rich`

See [CLAUDE.md](CLAUDE.md) for full architecture + model IDs.

## Status

Scaffold phase — only `gemini.understand` has a reference implementation. All other paths raise `NotImplementedError`.
