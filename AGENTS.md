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
           provider: str | None = None, tier: str = "poor",
           max_tokens: int = 2048,
           model: str | None = None) -> dict

generate(media_type: Literal["image", "video"], prompt: str,
         provider: str | None = None, tier: str = "poor",
         reference_image_url: str | None = None,
         job_id: str | None = None,
         output_mode: Literal["base64", "path", "both"] = "both",
         aspect_ratio: str = "16:9",
         duration_seconds: int = 8,
         model: str | None = None) -> dict

config(action: str, key: str | None = None, value: str | None = None) -> dict

help(topic: str = "understand") -> str
```

`model` (optional, litellm `provider/model` format) overrides the provider/tier
catalog — bypasses `VALID_PROVIDERS` + the model-ID table for open passthrough.
Any litellm `provider/model` works via passthrough even if not in the model-ID table.

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
| grok | understand | image | poor | `grok-4.20-0309-non-reasoning` |
| grok | understand | image | rich | `grok-4.20-0309-reasoning` |
| grok | understand | video | — | Not supported (prod 4.20-0309-v2 image-only) |
| grok | generate | image | poor | `grok-imagine-image` (Aurora) |
| grok | generate | image | rich | `grok-imagine-image-pro` |
| grok | generate | video | — | `grok-imagine-video` (single-tier) |

## Transport modes

Dispatched in `src/imagine_mcp/__main__.py:41-64`:

- **Default**: `stdio` — `build_app().run(transport="stdio")` on stdin/stdout (single-user, no daemon). Env-only creds; exits 1 if all three API keys missing.
- **Opt-in**: `http` — enabled by `--http`, `MCP_TRANSPORT=http`, or `TRANSPORT_MODE=http`. Runs mcp-core `run_http_server` (`src/imagine_mcp/server.py:314,341`), always multi-user; credentials via browser form at `/authorize`.

## Credentials

3 API keys (all optional — server runs in degraded mode with missing creds):

- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `XAI_API_KEY`

Priority (`src/imagine_mcp/relay_setup.py`): env var > `config.enc` (via mcp-core) > optional `MCP_RELAY_URL` relay fetch > degraded mode. (Stdio mode reads env vars only.)

## LLM backend (litellm passthrough)

`understand` (all providers) dispatches through `mcp_core.llm` (litellm library-mode
passthrough, `n24q02m-mcp-core[llm]`) with OpenAI-format vision messages. Pass
`model="provider/model"` for open passthrough (capability-checked via
`mcp_core.llm.check_capability`, graceful on registry-missing).

- `UNDERSTAND_MODELS` -- ordered model chain for understand, CSV `provider/model,...`;
  order = litellm fallback. Provider inferred from the model prefix. Empty/unset =
  understand off (provider/tier catalog default). imagine has NO local fallback.
- API keys follow the litellm convention `<PROVIDER>_API_KEY`. The 6 providers the
  server suggests for the understand chain:

  | model prefix | key env var | get it at |
  |---|---|---|
  | `gemini/` | `GEMINI_API_KEY` | aistudio.google.com/apikey |
  | `openai/` (or bare) | `OPENAI_API_KEY` | platform.openai.com |
  | `jina_ai/` | `JINA_AI_API_KEY` | jina.ai/api-key |
  | `cohere/` | `COHERE_API_KEY` | dashboard.cohere.com |
  | `xai/` | `XAI_API_KEY` | console.x.ai |
  | `anthropic/` | `ANTHROPIC_API_KEY` | console.anthropic.com |

  For any other litellm provider, see https://docs.litellm.ai/docs/providers/<provider> for its `<PROVIDER>_API_KEY` name.

**Generation stays NATIVE** (deferred 2026-06-11): gemini image+Veo (`google-genai`),
openai image (OpenAI SDK), grok image/video (raw httpx; xAI gen = verified litellm gap).

- `LLM_API_BASE` -- custom OpenAI-compatible base URL for understand (SSRF-vetted via
  `mcp_core.http.vet_api_base`).
- `LLM_API_BASE_ALLOW_PRIVATE=1` -- single-user escape for private/loopback api_base.

### Manual config example

```json
{
  "mcpServers": {
    "imagine": {
      "command": "uvx", "args": ["imagine-mcp"],
      "env": {
        "UNDERSTAND_MODELS": "gemini/gemini-3.1-pro-preview,openai/gpt-5.4",
        "GEMINI_API_KEY": "AIza_xxx",
        "OPENAI_API_KEY": "sk_xxx"
      }
    }
  }
}
```

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
