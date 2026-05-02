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
| grok | understand | image | poor | `grok-4.20-0309-non-reasoning` |
| grok | understand | image | rich | `grok-4.20-0309-reasoning` |
| grok | understand | video | — | Not supported (prod 4.20-0309-v2 image-only) |
| grok | generate | image | poor | `grok-imagine-image` (Aurora) |
| grok | generate | image | rich | `grok-imagine-image-pro` |
| grok | generate | video | — | `grok-imagine-video` (single-tier) |

## Transport modes (parity with wet/mnemo/crg category `http local relay`)

- **Default**: `http local relay` -- `run_local_server` on 127.0.0.1:<port>, credential form at `/authorize`.
- **Alternative**: `http remote relay (self-host)` -- `MCP_MODE=remote-relay` + `MCP_RELAY_URL=<your-deployed-url>`; server pulls creds from your relay, then serves MCP protocol locally. n24q02m does not host a public `imagine-mcp.n24q02m.com` (see mode-matrix.md section 2.5).
- **Stdio transport**: `--stdio` or `MCP_TRANSPORT=stdio` -- `run_smart_stdio_proxy` spawns a local daemon (same backend as http local relay) and bridges stdin/stdout. Not a separate mode; it is a transport wrapper on top of the daemon.

## Credentials

3 API keys (all optional — server runs in degraded mode with missing creds):

- `XAI_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY` (renamed from `GOOGLE_AI_STUDIO_API_KEY` 2026-04-26 for parity with wet/mnemo/crg)

Source priority: env var > `config.enc` (via mcp-core) > relay setup > degraded mode.

Auto-fallback provider (when `understand`/`generate` is called without an
explicit `provider`): the first key present in this order wins —
`XAI_API_KEY` → `grok`, `OPENAI_API_KEY` → `openai`, `GEMINI_API_KEY` →
`gemini`. Gemini is last because Google AI Studio accounts can be
billing-locked at the org level (403 PERMISSION_DENIED) without warning. If
no key is configured the dispatcher raises `CredentialMissingError`.

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

