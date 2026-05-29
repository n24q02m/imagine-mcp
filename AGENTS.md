# imagine-mcp

Production-grade MCP server for image/video understanding and generation across Gemini, OpenAI, and Grok.

## Architecture

- **Tools** (4 total, N+2 layout): `understand`, `generate`, `config`, `help`
- **Providers**: `gemini` | `openai` | `grok`
- **Tiers**: `poor` (cheap/fast) | `rich` (high quality)
- **Media types**: `image` | `video`

## Tool signatures

```python
understand(media_urls: list[str], prompt: str,
           provider: str = "gemini", tier: str = "poor",
           max_tokens: int = 2048) -> dict

generate(media_type: Literal["image", "video"], prompt: str,
         provider: str = "gemini", tier: str = "poor",
         reference_image_url: str | None = None,
         job_id: str | None = None,
         output_mode: Literal["base64", "path", "both"] = "both",
         aspect_ratio: str = "16:9",
         duration_seconds: int = 8) -> dict

config(action: str, key: str | None = None, value: str | None = None) -> dict

help(topic: str = "understand") -> str
```

## Model IDs (verified 2026-04-18; rank from Artificial Analysis + LMArena, refreshed weekly)

For the authoritative leaderboard-sorted table see [`docs/models.md`](docs/models.md) (auto-generated).

| Provider | Action | Media | Tier | Model ID |
|----------|--------|:-----:|:----:|----------|
| gemini | understand | image/video | poor | `gemini-3.1-flash-lite-preview` |
| gemini | understand | image/video | rich | `gemini-3.1-pro-preview` |
| gemini | generate | image | poor | `gemini-3.1-flash-image-preview` (Nano Banana 2) |
| gemini | generate | image | rich | `gemini-3-pro-image-preview` (Nano Banana Pro; cross-gen) |
| gemini | generate | video | poor | `veo-3.1-lite-generate-preview` |
| gemini | generate | video | rich | `veo-3.1-generate-preview` |
| openai | understand | image | poor | `gpt-5.4-mini` |
| openai | understand | image | rich | `gpt-5.4` |
| openai | understand | video | — | Not supported (extract frames or use gemini) |
| openai | generate | image | poor | `gpt-image-1-mini` |
| openai | generate | image | rich | `gpt-image-1.5` (cross-gen; no gpt-image-1.5-mini) |
| openai | generate | video | — | Not supported (Sora 2 API shutdown 2026-09-24) |
| grok | understand | image | poor | `grok-3-vision` |
| grok | understand | image | rich | `grok-3-vision` |
| grok | understand | video | — | Not supported (prod 4.20-0309-v2 image-only) |
| grok | generate | image | poor | `grok-imagine-image` (Aurora) |
| grok | generate | image | rich | `grok-imagine-image-pro` |
| grok | generate | video | — | `grok-imagine-video` (single-tier) |

## Transport modes

- **Default**: `http local relay mode` — `run_local_server` on 127.0.0.1:<port>, credentials via browser form
- **Alternative**: `stdio proxy mode` — spawn with `--stdio` or `MCP_MODE=stdio-proxy`

## Credentials

3 API keys (all optional — server runs in degraded mode with missing creds):

- `GOOGLE_AI_STUDIO_API_KEY`
- `OPENAI_API_KEY`
- `XAI_API_KEY`

Priority: env var > `config.enc` (via mcp-core) > relay setup > degraded mode.

## Install

```bash
# With uvx (recommended)
uvx imagine-mcp

# Docker
docker run -it --rm ghcr.io/n24q02m/imagine-mcp:latest
```

## Commits

`fix:` and `feat:` prefixes only. English for commits, documentation, and code.

## License

MIT. See [`LICENSE`](LICENSE).
