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

`model` (litellm `provider/model` format) selects the model directly for open
passthrough -- there is no hardcoded model catalog (#461). For `understand` it
is required unless the `UNDERSTAND_MODELS` env chain is set (no built-in
default). For `generate` it overrides the `GENERATE_MODELS` chain and the
provider's own minimal built-in default.

## Model selection

No hardcoded model-ID catalog: `understand` is caller-driven only (explicit
`model=` or the `UNDERSTAND_MODELS` chain; litellm passthrough, any provider).
`generate` stays native per provider (Gemini / OpenAI / Grok) with a minimal
built-in default per tier, overridable via `model=` or `GENERATE_MODELS`.
Capability gaps: OpenAI has no video understanding or generation; Grok
production has no video understanding.

## Transport modes

Dispatched in `src/imagine_mcp/__main__.py:41-64`:

- **Default**: `stdio` — `build_app().run(transport="stdio")` on stdin/stdout (single-user, no daemon). Env-only creds; exits 1 if all three API keys missing.
- **Opt-in**: `http` — enabled by `--http`, `MCP_TRANSPORT=http`, or `TRANSPORT_MODE=http`. Runs mcp-core `run_http_server` (`src/imagine_mcp/server.py:314,341`), always multi-user; credentials via browser form at `/authorize`.

## Credentials

3 API keys (all optional — server runs in degraded mode with missing creds):

- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `XAI_API_KEY`

Priority (`src/imagine_mcp/relay_setup.py`): env var > `~/.imagine-mcp/config.json` (per-plugin store, via mcp-core) > optional `MCP_RELAY_URL` relay fetch > degraded mode. (Stdio mode reads env vars only.)

## LLM backend (litellm passthrough)

`understand` (all providers) dispatches through `mcp_core.llm` (litellm library-mode
passthrough, `n24q02m-mcp-core[llm]`) with OpenAI-format vision messages. Pass
`model="provider/model"` for open passthrough (capability-checked via
`mcp_core.llm.check_capability`, graceful on registry-missing).

- `UNDERSTAND_MODELS` -- ordered model chain for understand, CSV `provider/model,...`;
  order = litellm fallback. Provider inferred from the model prefix. Empty/unset +
  no explicit `model` = no built-in default -- raises `ModelNotConfiguredError`
  (#461). imagine has NO local fallback.
- API keys follow the litellm convention `<PROVIDER>_API_KEY`. The 7 providers the
  server suggests for the understand chain:

  | model prefix | key env var | get it at |
  |---|---|---|
  | `gemini/` | `GEMINI_API_KEY` | aistudio.google.com/apikey |
  | `vertex_express/` | `GOOGLE_VERTEX_EXPRESS_API_KEY` | cloud.google.com/vertex-ai/generative-ai/docs/start/express-mode/overview |
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
        "UNDERSTAND_MODELS": "gemini/<model-id>,openai/<model-id>",
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
