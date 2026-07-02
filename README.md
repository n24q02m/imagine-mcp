# imagine-mcp

mcp-name: io.github.n24q02m/imagine-mcp

**Image and video understanding + generation for AI agents -- across Gemini, OpenAI, and Grok.**

<!-- Badge Row 1: Status -->
[![CI](https://github.com/n24q02m/imagine-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/n24q02m/imagine-mcp/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/n24q02m/imagine-mcp/graph/badge.svg)](https://codecov.io/gh/n24q02m/imagine-mcp)
[![PyPI](https://img.shields.io/pypi/v/imagine-mcp?logo=pypi&logoColor=white)](https://pypi.org/project/imagine-mcp/)
[![Docker](https://img.shields.io/docker/v/n24q02m/imagine-mcp?label=docker&logo=docker&logoColor=white&sort=semver)](https://hub.docker.com/r/n24q02m/imagine-mcp)
[![License: MIT](https://img.shields.io/github/license/n24q02m/imagine-mcp)](LICENSE)

<!-- Badge Row 2: Tech -->
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](#)
[![FastMCP](https://img.shields.io/badge/FastMCP-purple?logo=anthropic&logoColor=white)](#)
[![MCP](https://img.shields.io/badge/MCP-000000?logo=anthropic&logoColor=white)](#)
[![semantic-release](https://img.shields.io/badge/semantic--release-e10079?logo=semantic-release&logoColor=white)](https://github.com/python-semantic-release/python-semantic-release)
[![Renovate](https://img.shields.io/badge/renovate-enabled-1A1F6C?logo=renovatebot&logoColor=white)](https://developer.mend.io/)

<!-- BEGIN: AUTO-GENERATED-CROSS-PROMO -->
<details>
  <summary><strong>Sister projects from n24q02m</strong> (click to expand)</summary>

| Project | Tagline | Tag |
|---|---|---|
| [better-code-review-graph](https://github.com/n24q02m/better-code-review-graph) | Knowledge graph for token-efficient code reviews -- semantic search and call-... | MCP |
| [better-email-mcp](https://github.com/n24q02m/better-email-mcp) | IMAP/SMTP email for AI agents -- read, send, organize folders, and manage att... | MCP |
| [better-godot-mcp](https://github.com/n24q02m/better-godot-mcp) | Composite MCP server for Godot Engine -- 17 composite tools for AI-assisted g... | MCP |
| [better-notion-mcp](https://github.com/n24q02m/better-notion-mcp) | Markdown-first Notion for AI agents -- pages, databases, blocks, and comments... | MCP |
| [better-telegram-mcp](https://github.com/n24q02m/better-telegram-mcp) | Telegram for AI agents -- messages, chats, media, and contacts across both bo... | MCP |
| [claude-plugins](https://github.com/n24q02m/claude-plugins) | Claude Code plugin marketplace for the n24q02m MCP servers -- install web sea... | Marketplace |
| [imagine-mcp](https://github.com/n24q02m/imagine-mcp) | Image and video understanding + generation for AI agents -- across Gemini, Op... | MCP |
| [jules-task-archiver](https://github.com/n24q02m/jules-task-archiver) | Chrome Extension for bulk operations on Jules tasks via batchexecute API -- a... | Tooling |
| [mcp-core](https://github.com/n24q02m/mcp-core) | Shared foundation for building MCP servers -- Streamable HTTP transport, OAut... | MCP |
| [mnemo-mcp](https://github.com/n24q02m/mnemo-mcp) | Persistent AI memory with hybrid search and embedded sync. Open, free, unlimi... | MCP |
| [qwen3-embed](https://github.com/n24q02m/qwen3-embed) | Lightweight Qwen3 text embedding and reranking via ONNX Runtime and GGUF | Library |
| [skret](https://github.com/n24q02m/skret) | Secrets without the server. | CLI |
| [tacet](https://github.com/n24q02m/tacet) | TACET: a self-distilling neuro-symbolic cascade that amortises LLM cost in kn... | Tooling |
| [web-core](https://github.com/n24q02m/web-core) | Shared web infrastructure package for search, scraping, HTTP security, and st... | Library |
| [wet-mcp](https://github.com/n24q02m/wet-mcp) | Open-source MCP server for AI agents: web search, content extraction, and lib... | MCP |

</details>
<!-- END: AUTO-GENERATED-CROSS-PROMO -->

## Table of contents

- [Features](#features)
- [Install](#install)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Tools](#tools)
- [Comparison](#comparison)
- [Security](#security)
- [Build from Source](#build-from-source)
- [Deploy to Cloudflare](#deploy-to-cloudflare)
- [Trust Model](#trust-model)
- [Contributing](#contributing)
- [License](#license)



<a href="https://glama.ai/mcp/servers/n24q02m/imagine-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/n24q02m/imagine-mcp/badge" alt="imagine-mcp server" />
</a>

## Features

- **Multimodal understanding** -- Describe, classify, or reason over images and videos (Gemini handles mixed image + video in one call)
- **Image generation** -- Text-to-image and image-to-image (edit / inpaint) across Gemini Imagen, OpenAI gpt-image, Grok Imagine
- **Video generation** -- Text-to-video and image-to-video (Gemini Veo 3.1, Grok Imagine Video)
- **3 providers x 2 tiers** -- Same interface for `gemini` / `openai` / `grok` at `poor` (cheap/fast) or `rich` (high quality); swap via parameter
- **Leaderboard-ranked models** -- Provider ordering auto-refreshed weekly from Artificial Analysis + LMArena leaderboards
- **Degraded mode** -- Server starts with zero credentials and surfaces remaining providers as you add keys
- **Response cache** -- Disk-based caching of `understand` responses with configurable TTL
- **Dual transport** -- pure stdio with provider env vars (default) or HTTP multi-user with paste-token relay form

## Install

Run with [`uvx`](https://docs.astral.sh/uv/) (no install step) or pull the container image:

```bash
# uvx -- recommended, runs the published PyPI package
uvx imagine-mcp

# Docker
docker run -it --rm ghcr.io/n24q02m/imagine-mcp:latest
```

Add it to an MCP client by pointing the client at the `uvx imagine-mcp` command and
supplying at least one provider key (see [Configuration](#configuration)):

```json
{
  "mcpServers": {
    "imagine": {
      "command": "uvx",
      "args": ["imagine-mcp"],
      "env": { "GEMINI_API_KEY": "AIza..." }
    }
  }
}
```

For per-client snippets (Claude Code, Codex, Gemini CLI, Cursor, Windsurf) and the
browser-based HTTP setup, see the [Setup docs](https://mcp.n24q02m.com/servers/imagine-mcp/setup/).

**Install with an AI agent** -- paste this to your AI coding agent:

> Install MCP server `imagine-mcp` following the steps at  
> https://raw.githubusercontent.com/n24q02m/claude-plugins/main/plugins/imagine-mcp/setup-with-agent.md

## Configuration

Two transports (default `stdio`; opt into `http` with `--http`, `MCP_TRANSPORT=http`,
or `TRANSPORT_MODE=http`):

- **stdio** (default) -- single-user, reads credentials from env vars only. Exits if
  none of the three provider keys are set.
- **http** -- HTTP daemon. Local self-host on `127.0.0.1` by default, or multi-user
  remote (per-JWT-sub credential isolation) when `PUBLIC_URL` + `MCP_DCR_SERVER_SECRET`
  are set. In HTTP mode credentials are entered through a browser form at `/authorize`.

### Provider keys

All optional -- the server starts in degraded mode and surfaces whichever providers
have a key. Set at least one.

| Env var | Provider | Get a key at |
|---|---|---|
| `GEMINI_API_KEY` | Gemini (image + video) | aistudio.google.com/apikey |
| `OPENAI_API_KEY` | OpenAI (image) | platform.openai.com/api-keys |
| `XAI_API_KEY` | Grok / xAI (image + video) | console.x.ai |

When a tool is called without an explicit `provider`, the first key present wins in the
order `XAI_API_KEY` -> `OPENAI_API_KEY` -> `GEMINI_API_KEY`.

### Model chains (optional)

Override the built-in provider/tier catalog with explicit model chains. Each is a CSV of
litellm `provider/model` entries; the order is the fallback order.

| Env var | Purpose |
|---|---|
| `UNDERSTAND_MODELS` | Ordered model chain for `understand` (litellm fallback). Empty -> catalog default. |
| `GENERATE_MODELS` | Ordered model chain for `generate`. The first entry selects the native provider + model. Empty -> catalog default. |
| `GENERATE_PROVIDER_PRIORITY` | CSV of provider names reordering generation auto-fallback. Defaults to `grok,openai,gemini`. |

Understanding is routed through litellm (`provider/model` passthrough), so any litellm
provider works -- supply that provider's `<PROVIDER>_API_KEY`. Generation stays on the
native provider SDKs (Gemini, OpenAI, Grok). Example:

```json
{
  "mcpServers": {
    "imagine": {
      "command": "uvx",
      "args": ["imagine-mcp"],
      "env": {
        "UNDERSTAND_MODELS": "gemini/gemini-3.1-pro-preview,openai/gpt-5.4",
        "GEMINI_API_KEY": "AIza...",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Runtime knobs

`config(action="set", key=..., value=...)` adjusts `log_level`, `default_provider`,
`default_tier`, and `cache_ttl_seconds` at runtime.

## Documentation

Full docs at **[mcp.n24q02m.com/servers/imagine-mcp/setup/](https://mcp.n24q02m.com/servers/imagine-mcp/setup/)**:

- [Setup](https://mcp.n24q02m.com/servers/imagine-mcp/setup/) -- install methods for Claude Code, Codex, Gemini CLI, Cursor, Windsurf, mcp.json
- [Modes overview](https://mcp.n24q02m.com/get-started/modes-overview/) -- stdio / local-relay / remote-relay / remote-oauth
- [Multi-user setup](https://mcp.n24q02m.com/get-started/multi-user/) -- per-JWT-sub credential model

## Tools

| Tool | Actions | Description |
|:-----|:--------|:------------|
| `understand` | -- | Describe or reason over one or more image/video URLs. `media_urls: list[str]`, `prompt: str`, `provider`, `tier`, `max_tokens`. |
| `generate` | -- | Generate an image or video from a text prompt. `media_type: image\|video`, optional `reference_image_url`, optional `job_id` (video poll), `aspect_ratio`, `duration_seconds`. |
| `config` | `open_relay`, `relay_status`, `relay_skip`, `relay_reset`, `relay_complete`, `warmup`, `status`, `set`, `cache_clear` | Credential + runtime config: open relay form, check credential state, set runtime knobs (log level, default provider, TTL), clear response cache. |
| `help` | -- | Full Markdown documentation for `understand`, `generate`, or `config` topics. |
| `config__open_relay` | -- | Framework-injected helper (mcp-core) equivalent to `config(action="open_relay")`; opens the browser credential form. |

Model IDs per provider x action x tier are leaderboard-ranked; see [`docs/models.md`](docs/models.md) (auto-regenerated from `src/imagine_mcp/models.py`).

## Comparison

How imagine-mcp stacks up against direct competitors in each pillar:

| Capability | imagine-mcp | EverArt MCP | fal.ai MCP | Replicate Flux MCP |
|---|---|---|---|---|
| Image/video understanding | Yes (describe / classify / reason over image + video URLs) | No | No | No |
| Image generation | Yes (text-to-image + image-to-image via `reference_image_url`) | Yes (single `generate_image`) | Yes (text/image-to-image, edit, inpaint) | Yes (single `generate_image`) |
| Video generation | Yes (text-to-video + image-to-video, async `job_id` poll) | No | Yes (text/image-to-video) | No |
| Multi-provider backends | Yes (Gemini / OpenAI / Grok, auto-fallback) | No (EverArt only) | No (fal.ai only) | No (Replicate Flux only) |
| Quality/cost tiers | Yes (`poor` cheap-fast vs `rich` high-quality per provider) | No | No | No |
| Self-hostable / open source | Yes (MIT, stdio + HTTP self-host) | Yes (MIT, archived) | Yes (MIT) | Yes (MIT, archived) |

## Security

- **SSRF + LFI prevention** -- All `media_urls` and `reference_image_url` are validated at the dispatch boundary; only `http://` and `https://` schemes reach the providers. `file://`, `ftp://`, `gopher://`, and scheme-less URLs are rejected.
- **No credentials in errors** -- Provider-side errors are sanitized before being returned.
- **Degraded start** -- Missing credentials do not prevent the server from starting; affected actions surface actionable errors instead of crashing at boot.
- **Credential storage** -- Credentials submitted through the browser credential form are stored encrypted via `mcp-core` (AES-GCM, machine-bound key) at `~/.imagine-mcp/config.json`.

## Build from Source

```bash
git clone https://github.com/n24q02m/imagine-mcp.git
cd imagine-mcp
mise run setup      # or: uv sync --group dev
mise run dev        # run the server in stdio mode (add --http for the HTTP daemon)
```

## Deploy to Cloudflare

[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/n24q02m/imagine-mcp)

Run your own imagine instance serverless on Cloudflare (Worker + Container + KV). Storage
is KV-only -- the per-user credential vault lives in KV, and generation returns base64 only
because the container filesystem is ephemeral (`IMAGINE_OUTPUT_MODE=base64`).

**Prerequisites:** a Cloudflare account on the **Workers Paid plan** -- required for Containers (the Cloudflare free tier does not include Containers) -- and the `wrangler` CLI.

1. `git clone https://github.com/n24q02m/imagine-mcp && cd imagine-mcp`
2. `wrangler login`
3. Create the KV namespace (imagine is KV-only -- no D1 or Vectorize), then paste the
   returned id into `wrangler.jsonc` (the `<imagine-kv-namespace-id>` placeholder):
   ```
   wrangler kv namespace create imagine-kv
   ```
4. Push the container image to your Cloudflare managed registry (CF Containers cannot pull
   from external registries directly), then set `<YOUR_ACCOUNT_ID>` in `wrangler.jsonc`:
   ```
   docker pull ghcr.io/n24q02m/imagine-mcp:beta
   docker tag ghcr.io/n24q02m/imagine-mcp:beta imagine-mcp:beta
   wrangler containers push imagine-mcp:beta   # prints registry.cloudflare.com/<ACCOUNT_ID>/imagine-mcp:beta
   ```
5. Point the remaining `wrangler.jsonc` placeholders at your own domain: `<YOUR_PUBLIC_URL>`
   (the `vars.PUBLIC_URL`, e.g. `https://imagine.example.com`) and `<YOUR_WORKER_DOMAIN>`
   (the `routes` custom-domain pattern, e.g. `imagine.example.com`).
6. Set secrets. `CREDENTIAL_SECRET` (stable JWT signing key + per-user vault key) and
   `MCP_DCR_SERVER_SECRET` (proof of an intentional multi-user deploy) are required;
   `MCP_RELAY_PASSWORD` gates the browser setup form's login. Provider keys are optional
   server defaults -- users normally paste their own through the setup form instead:
   ```
   wrangler secret put CREDENTIAL_SECRET
   wrangler secret put MCP_DCR_SERVER_SECRET
   wrangler secret put MCP_RELAY_PASSWORD
   wrangler secret put GEMINI_API_KEY       # optional provider default
   wrangler secret put OPENAI_API_KEY       # optional provider default
   wrangler secret put XAI_API_KEY          # optional provider default
   ```
7. `wrangler deploy`, then open your Worker domain and finish setup in the browser relay form.

The `http` container image already runs multi-user (`MCP_TRANSPORT=http` is baked into the
image target). Storage maps to Cloudflare via `MCP_STORAGE_BACKEND=cf-kv` (encrypted
credential vault) with `IMAGINE_OUTPUT_MODE=base64`, which forces base64 responses so no
media path is written to the ephemeral container filesystem.

## Trust Model

This plugin implements **TC-Local** (machine-bound, single trust principal). See [mcp-core trust model](https://mcp.n24q02m.com/servers/mcp-core/trust-model/) for full classification.

| Mode | Storage | Encryption | Who can read your data? |
|---|---|---|---|
| stdio (default) | `~/.imagine-mcp/config.json` | AES-GCM, machine-bound key | Only your OS user (file perm 0600) |
| HTTP self-host | Same as stdio | Same | Only you (admin = user) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development workflow, commit convention, and release process. Issues + Discussions welcome.

## License

MIT -- see [LICENSE](LICENSE).