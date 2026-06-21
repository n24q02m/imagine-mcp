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

Two transports, dispatched in `src/imagine_mcp/__main__.py:41-64`:

- **Default**: `stdio` -- `build_app().run(transport="stdio")` on stdin/stdout (single-user, no daemon, no browser). Reads creds from env vars only; exits 1 if all three of `GEMINI_API_KEY`/`OPENAI_API_KEY`/`XAI_API_KEY` are missing. Universal MCP client compatibility.
- **Opt-in**: `http` -- enabled by `--http` flag, `MCP_TRANSPORT=http`, or `TRANSPORT_MODE=http`. Runs `run_http()` -> mcp-core `run_http_server` (`src/imagine_mcp/server.py:314,341`), always multi-user / remote-style. Set `PUBLIC_URL` + `MCP_DCR_SERVER_SECRET` to bind publicly with per-JWT-sub credential isolation; otherwise serves on `127.0.0.1:<port>` for local self-host. Credentials set via the browser form at `/authorize`.

## Credentials

3 API keys (all optional — server runs in degraded mode with missing creds):

- `XAI_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY` (renamed from `GOOGLE_AI_STUDIO_API_KEY` 2026-04-26 for parity with wet/mnemo/crg)

Source priority (`src/imagine_mcp/relay_setup.py`): env var > `~/.imagine-mcp/config.json` (per-plugin store, via mcp-core) > optional `MCP_RELAY_URL` remote-relay fetch > degraded mode. (Stdio mode reads env vars only.)

Auto-fallback provider (when `understand`/`generate` is called without an
explicit `provider`): the first key present in this order wins —
`XAI_API_KEY` → `grok`, `OPENAI_API_KEY` → `openai`, `GEMINI_API_KEY` →
`gemini`. Gemini is last because Google AI Studio accounts can be
billing-locked at the org level (403 PERMISSION_DENIED) without warning. If
no key is configured the dispatcher raises `CredentialMissingError`.

## LLM backend (litellm passthrough)

**Understanding** (`understand`, all providers) dispatches through `mcp_core.llm`
(litellm library-mode passthrough, `n24q02m-mcp-core[llm]`) using OpenAI-format
vision messages — no native provider SDK for the understand path. Open passthrough:
pass `model="provider/model"` to bypass the catalog (any litellm model works;
capability-checked via `mcp_core.llm.check_capability`, graceful on registry-missing).

- `UNDERSTAND_MODELS` -- ordered model chain for the understand path, CSV
  `provider/model,provider/model`; order = litellm fallback (first entry is the
  primary model, the rest are fallbacks). Provider is inferred from the model
  prefix. **Empty/unset = understand off** (falls back to the provider/tier
  catalog default). imagine has NO local fallback. In multi-user HTTP mode the
  chain is resolved per-sub (from the relay-submitted config, never
  `os.environ`); single-user / stdio reads the env var.
- API keys follow the litellm convention `<PROVIDER>_API_KEY`. The 6 providers
  the server suggests for the understand chain:

  | model prefix | key env var | get it at |
  |---|---|---|
  | `gemini/` | `GEMINI_API_KEY` | aistudio.google.com/apikey |
  | `openai/` (or bare) | `OPENAI_API_KEY` | platform.openai.com |
  | `jina_ai/` | `JINA_AI_API_KEY` | jina.ai/api-key |
  | `cohere/` | `COHERE_API_KEY` | dashboard.cohere.com |
  | `xai/` | `XAI_API_KEY` | console.x.ai |
  | `anthropic/` | `ANTHROPIC_API_KEY` | console.anthropic.com |

  For any other litellm provider (used via env passthrough), see https://docs.litellm.ai/docs/providers/<provider> for its `<PROVIDER>_API_KEY` name.

**Generation** stays NATIVE (deferred 2026-06-11, credential-gated probe):
gemini image + Veo video via `google-genai`, openai image via the OpenAI SDK,
grok image/video via raw httpx x.ai endpoints (xAI generation is a verified
litellm gap). `google-genai` + `openai` deps are retained for these paths.

- `GENERATE_MODELS` -- ordered model chain for generation, CSV
  `provider/model,provider/model`. The FIRST entry selects the native provider
  from its `provider/` prefix AND overrides the catalog `model_id` with its
  model segment (generation is never routed through litellm). **Empty/unset =
  use the provider/tier catalog default.** Sub-aware (per-sub in multi-user
  HTTP; env var single-user / stdio).
- `GENERATE_PROVIDER_PRIORITY` -- optional CSV of provider names
  (`grok,openai,gemini`) reordering the generation auto-fallback when no
  explicit provider and no `GENERATE_MODELS` chain are given. Defaults to the
  native order (XAI, OpenAI, Gemini). Sub-aware like the chains above.

- `LLM_API_BASE` -- custom OpenAI-compatible base URL for the understand path
  (optional; vetted through `mcp_core.http.vet_api_base` SSRF guard).
- `LLM_API_BASE_ALLOW_PRIVATE=1` -- single-user escape to allow a private/loopback
  `api_base` (ignored in multi-user mode when `PUBLIC_URL` is set).

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

## E2E

Driven by `mcp-core/scripts/e2e/` (matrix-locked, 15 configs). Run a single config from this repo via `make e2e` (proxy) or directly:

```
cd ../mcp-core && uv run --project scripts/e2e python -m e2e.driver <config-id>
```

Configs for this repo: `imagine`.

t2-non-interaction: paste optional LLM provider keys (Gemini/OpenAI/xAI). 2026-04-24 env rename ``GOOGLE_AI_STUDIO_API_KEY`` -> ``GEMINI_API_KEY``.

Tier policy:

- **T0** (precommit + CI on PR / main push) - runs without upstream identity. Skret keys not required.
- **T2 non-interaction** (`make e2e-config CONFIG=<id>` locally) - driver pre-fills relay form from skret AWS SSM `/imagine-mcp/prod` (`ap-southeast-1`). No user gate.
- **T2 interaction** - driver fills relay form, then prints upstream user-gate URL; user signs in / types OTP at provider. Driver enforces per-flow timeouts (device-code 900s, oauth-redirect 300s, browser-form 600s) and emits `[poll] elapsed=Xs remaining=Ys status=<body>` every 30s. On timeout, container logs + last `setup-status` are saved to `<tmp>/e2e-diag/` BEFORE teardown for post-mortem.

Multi-user remote mode (deployment property; not a separate config) requires `MCP_DCR_SERVER_SECRET` in the same skret namespace - driver refuses to start the container without it when `PUBLIC_URL` is set.

References: `mcp-core/scripts/e2e/matrix.yaml`, `~/.claude/skills/mcp-dev/references/e2e-full-matrix.md` (harness-readiness gate), `~/.claude/skills/mcp-dev/references/secrets-skret.md` (per-server credential layout), `~/.claude/skills/mcp-dev/references/multi-user-pattern.md` (per-JWT-sub isolation).

## Cloudflare serverless mode

imagine-mcp runs serverless on Cloudflare (Worker + Container + KV-only). The
only externalised state is the per-sub credential vault (KV); generation is
returned base64-only because the container FS is ephemeral.

| env var | value | purpose |
|---|---|---|
| `MCP_TRANSPORT` | `http` | container detection + multi-user mode |
| `PUBLIC_URL` | `https://imagine.n24q02m.com` | public bind + per-JWT-sub isolation |
| `MCP_STORAGE_BACKEND` | `cf-kv` | route PerPluginStore through KV |
| `MCP_KV_BASE_URL` | `http://kv.internal` | Worker outbound-handler virtual host |
| `IMAGINE_OUTPUT_MODE` | `base64` | force base64 output (no local media path) |
| `CREDENTIAL_SECRET` | (secret) | stable EdDSA JWT key (no disk) + per-sub vault key |
| `MCP_DCR_SERVER_SECRET` | (secret) | proof of intentional multi-user deploy |

`IMAGINE_OUTPUT_MODE=base64` overrides the `generate` tool's `output_mode` arg
so every request returns `image_base64` / `video_base64` and never an
`image_path` (the ephemeral container FS would lose the file on recreate).

ResponseCache (`cache.py`, diskcache) is NOT on the hot path -- `understand` /
`generate` never read/write it; it is only touched by `config(action="cache_clear")`,
which is a harmless no-op on the ephemeral FS. No KV migration needed.

`src/worker.ts` + `wrangler.jsonc` are copied from the frozen CF template
(`wet-mcp/docs/cf-template.md`), KV-only (no D1/Vectorize): `ImagineContainer` DO
+ `IMAGINE` binding, the `kv.internal` outbound handler off the public `fetch`
(security), and the 5 footguns. Live OAuth self-test: `scripts/cf_full_flow.py`.

