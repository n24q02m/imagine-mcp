# imagine-mcp

mcp-name: io.github.n24q02m/imagine-mcp

**Production-grade MCP server for image and video understanding + generation across Gemini, OpenAI, and Grok.**

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
| [better-code-review-graph](https://github.com/n24q02m/better-code-review-graph) | Knowledge graph for token-efficient code reviews -- fixed search, configurabl... | MCP |
| [better-email-mcp](https://github.com/n24q02m/better-email-mcp) | IMAP/SMTP email server for AI agents -- 7 composite tools with multi-account ... | MCP |
| [better-godot-mcp](https://github.com/n24q02m/better-godot-mcp) | Composite MCP server for Godot Engine -- 17 mega-tools for AI-assisted game d... | MCP |
| [better-notion-mcp](https://github.com/n24q02m/better-notion-mcp) | Markdown-first Notion API server for AI agents -- 11 composite tools replacin... | MCP |
| [better-telegram-mcp](https://github.com/n24q02m/better-telegram-mcp) | MCP server for Telegram with dual-mode support: Bot API (httpx) for quick bot... | MCP |
| [claude-plugins](https://github.com/n24q02m/claude-plugins) | Full documentation: mcp.n24q02m.com — unified docs for all 8 servers + the mc... | Marketplace |
| [imagine-mcp](https://github.com/n24q02m/imagine-mcp) | Production-grade MCP server for image and video understanding + generation ac... | MCP |
| [jules-task-archiver](https://github.com/n24q02m/jules-task-archiver) | Chrome Extension for bulk operations on Jules tasks via batchexecute API -- a... | Tooling |
| [mcp-core](https://github.com/n24q02m/mcp-core) | Unified MCP Streamable HTTP 2025-11-25 transport, OAuth 2.1 Authorization Ser... | MCP |
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
- [Status](#status)
- [Documentation](#documentation)
- [Tools](#tools)
- [Comparison](#comparison)
- [Security](#security)
- [Build from Source](#build-from-source)
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

## Status

> **2026-05-02 -- Architecture stabilization update**
>
> Past months saw significant churn around credential handling and the daemon-bridge auto-spawn pattern. This caused multi-process races, browser tab spam, and inconsistent setup UX across plugins. **The architecture is now stable**: 2 clean modes (stdio + HTTP), no daemon-bridge layer, no auto-spawn from stdio.
>
> Apologies for the instability period. If you encountered issues with prior versions, please update to the latest release and follow the current [Setup docs](https://mcp.n24q02m.com/servers/imagine-mcp/setup/) -- most prior workarounds are no longer needed.
>
> **Related plugins from the same author**:
> - [wet-mcp](https://github.com/n24q02m/wet-mcp) -- Web search + content extraction
> - [mnemo-mcp](https://github.com/n24q02m/mnemo-mcp) -- Persistent AI memory
> - [better-notion-mcp](https://github.com/n24q02m/better-notion-mcp) -- Notion API
> - [better-email-mcp](https://github.com/n24q02m/better-email-mcp) -- Email management
> - [better-telegram-mcp](https://github.com/n24q02m/better-telegram-mcp) -- Telegram
> - [better-godot-mcp](https://github.com/n24q02m/better-godot-mcp) -- Godot Engine
> - [better-code-review-graph](https://github.com/n24q02m/better-code-review-graph) -- Code review knowledge graph
>
> All plugins share the same architecture -- install once, learn pattern transfers.

## Documentation

Full docs at **[mcp.n24q02m.com/servers/imagine-mcp/setup/](https://mcp.n24q02m.com/servers/imagine-mcp/setup/)**:

- [Setup](https://mcp.n24q02m.com/servers/imagine-mcp/setup/) -- install methods for Claude Code, Codex, Gemini CLI, Cursor, Windsurf, mcp.json
- [Modes overview](https://mcp.n24q02m.com/get-started/modes-overview/) -- stdio / local-relay / remote-relay / remote-oauth
- [Multi-user setup](https://mcp.n24q02m.com/get-started/multi-user/) -- per-JWT-sub credential model

**Install with AI agent** -- paste this to your AI coding agent:

> Install MCP server `imagine-mcp` following the steps at  
> https://raw.githubusercontent.com/n24q02m/claude-plugins/main/plugins/imagine-mcp/setup-with-agent.md

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
- **Relay transport** -- Credentials submitted through the local relay form are stored encrypted via `mcp-core` (`config.enc`, user-scoped `platformdirs`).

## Build from Source

```bash
git clone https://github.com/n24q02m/imagine-mcp.git
cd imagine-mcp
mise run setup      # or: uv sync --group dev
mise run dev        # run http local relay daemon
```

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