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

<a href="https://glama.ai/mcp/servers/n24q02m/imagine-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/n24q02m/imagine-mcp/badge" alt="imagine-mcp server" />
</a>

## Features

- **Multimodal understanding** -- Describe, classify, or reason over images and videos (Gemini handles mixed image + video in one call)
- **Image generation** -- Text-to-image and image-to-image (edit / inpaint) across Gemini Imagen, OpenAI gpt-image, Grok Imagine
- **Video generation** -- Text-to-video and image-to-video (Gemini Veo 3.1, Grok Imagine Video)
- **3 providers x 2 tiers** -- Same interface for `gemini` / `openai` / `grok` at `poor` (cheap/fast) or `rich` (high quality); swap via parameter
- **Leaderboard-ranked models** -- Provider ordering auto-refreshed weekly from Artificial Analysis + LMArena leaderboards
- **Zero-config onboarding** -- Browser-based credential relay form; no `.env` files or manual credential plumbing
- **Degraded mode** -- Server starts with zero credentials and surfaces remaining providers as you add keys
- **Response cache** -- Disk-based caching of `understand` responses with configurable TTL
- **Smart stdio proxy** -- stdio transport spawns a local HTTP daemon and forwards JSON-RPC frames, sharing credentials across invocations

## Setup

**With AI Agent** -- copy and send this to your AI agent:

> Please set up imagine-mcp for me. Follow this guide:
> https://raw.githubusercontent.com/n24q02m/imagine-mcp/main/docs/setup-with-agent.md

**Manual setup** -- follow [docs/setup-manual.md](docs/setup-manual.md)

## Tools

| Tool | Actions | Description |
|:-----|:--------|:------------|
| `understand` | -- | Describe or reason over one or more image/video URLs. `media_urls: list[str]`, `prompt: str`, `provider`, `tier`, `max_tokens`. |
| `generate` | -- | Generate an image or video from a text prompt. `media_type: image\|video`, optional `reference_image_url`, optional `job_id` (video poll), `aspect_ratio`, `duration_seconds`. |
| `config` | `open_relay`, `relay_status`, `relay_skip`, `relay_reset`, `relay_complete`, `warmup`, `status`, `set`, `cache_clear` | Credential + runtime config: open relay form, check credential state, set runtime knobs (log level, default provider, TTL), clear response cache. |
| `help` | -- | Full Markdown documentation for `understand`, `generate`, or `config` topics. |

Model IDs per provider x action x tier are leaderboard-ranked; see [`docs/models.md`](docs/models.md) (auto-regenerated from `src/imagine_mcp/models.py`).

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

This plugin implements **TC-Local** (machine-bound, single trust principal). See [mcp-core/docs/TRUST-MODEL.md](https://github.com/n24q02m/mcp-core/blob/main/docs/TRUST-MODEL.md) for full classification.

| Mode | Storage | Encryption | Who can read your data? |
|---|---|---|---|
| stdio (default) | `~/.imagine-mcp/config.json` | AES-GCM, machine-bound key | Only your OS user (file perm 0600) |
| HTTP self-host | Same as stdio | Same | Only you (admin = user) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development workflow, commit convention, and release process. Issues + Discussions welcome.

## License

MIT -- see [LICENSE](LICENSE).
