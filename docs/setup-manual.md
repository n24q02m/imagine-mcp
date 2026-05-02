# Imagine MCP -- Manual Setup Guide

> **2026-05-02 Update (v<auto>+)**: Plugin install (Method 1) now uses pure stdio mode with provider API key env vars.
> The previous "Zero-Config Relay" auto-spawn pattern has been removed.
> If you relied on the relay form to enter your keys, please:
> 1. Set at least one of `GEMINI_API_KEY` / `OPENAI_API_KEY` / `XAI_API_KEY` directly in plugin config (Method 1), OR
> 2. Switch to HTTP mode (Method 5 self-host) for browser-based paste-token setup.

## Prerequisites

- **Python** >= 3.13 (only if running from source; uvx and Docker bundle their own runtime)
- **At least one provider API key** -- Gemini, OpenAI, or xAI:
  - **Google AI Studio** (Gemini): https://aistudio.google.com/apikey
  - **OpenAI**: https://platform.openai.com/api-keys
  - **xAI** (Grok): https://console.x.ai

You can mix any subset. The server runs in degraded mode: providers without a key surface `CredentialMissingError` only when called.

## Method 1: Claude Code Plugin (Recommended)

Plugin marketplace install runs the server in **pure stdio mode** with provider env vars. No daemon-bridge, no auto-spawn, no relay form.

1. Get at least one provider API key (see Prerequisites above).
2. Open Claude Code in your terminal.
3. Install the plugin:
   ```bash
   /plugin marketplace add n24q02m/claude-plugins
   /plugin install imagine-mcp@n24q02m-plugins
   ```
4. Set at least one of `GEMINI_API_KEY` / `OPENAI_API_KEY` / `XAI_API_KEY` in the plugin config when prompted (or in your Claude Code settings).

## Method 2: uvx (Local Stdio with Env Vars)

Add to your MCP client configuration file:

**Claude Code** -- `.claude/settings.json` or `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "imagine": {
      "command": "uvx",
      "args": ["imagine-mcp"],
      "env": {
        "GEMINI_API_KEY": "AIza...",
        "OPENAI_API_KEY": "sk-...",
        "XAI_API_KEY": "xai-..."
      }
    }
  }
}
```

**Codex CLI** -- `~/.codex/config.toml`:
```toml
[mcp_servers.imagine]
command = "uvx"
args = ["imagine-mcp"]

[mcp_servers.imagine.env]
GEMINI_API_KEY = "AIza..."
OPENAI_API_KEY = "sk-..."
XAI_API_KEY = "xai-..."
```

**OpenCode** -- `opencode.json`:
```json
{
  "mcpServers": {
    "imagine": {
      "command": "uvx",
      "args": ["imagine-mcp"],
      "env": {
        "GEMINI_API_KEY": "AIza...",
        "OPENAI_API_KEY": "sk-...",
        "XAI_API_KEY": "xai-..."
      }
    }
  }
}
```

Supply only the keys you have -- any subset works. Restart your MCP client after editing the config.

## Method 3: Docker (Local Stdio)

```json
{
  "mcpServers": {
    "imagine": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GEMINI_API_KEY",
        "-e", "OPENAI_API_KEY",
        "-e", "XAI_API_KEY",
        "ghcr.io/n24q02m/imagine-mcp:latest"
      ]
    }
  }
}
```

Set the keys you have in your shell profile:
```bash
export GEMINI_API_KEY="AIza..."
export OPENAI_API_KEY="sk-..."
export XAI_API_KEY="xai-..."
```

## Why upgrade to HTTP mode?

Stdio is the default and works fine for single-user local setups. You may want to switch to HTTP mode (Method 5 self-host) when you need any of the following:

- **claude.ai web compatibility** -- claude.ai (the web UI) supports HTTP MCP servers but cannot spawn local stdio processes.
- **One server shared across N Claude Code sessions** -- a single HTTP instance serves multiple terminals/IDEs without re-spawning per session.
- **Browser-based paste-token setup** -- enter API keys in a relay form rather than editing JSON config; keys saved encrypted on disk per JWT subject.
- **Multi-device credential sync** -- save keys once on your laptop, the same self-hosted server serves your desktop / tablet without re-entering.
- **Multi-user team sharing** -- a self-hosted server can serve multiple users, each with their own isolated set of provider keys (per-JWT-sub).
- **Always-on persistent process for webhooks/agents** -- HTTP servers stay alive between sessions, enabling background work, scheduled agents, or webhook listeners.

## Method 4: HTTP Remote (Hosted)

Imagine MCP does **not** offer an n24q02m-hosted public instance -- provider API keys (Gemini / OpenAI / xAI) are paid per-token and would be billed to whoever runs the server. Use Method 5 (self-host) below to run your own HTTP instance, or stay on stdio for local single-user usage.

## Method 5: Self-Hosting HTTP Mode

Host your own multi-user paste-token server. Always multi-user (per-JWT-sub credential isolation). Each user pastes their own provider API keys via a browser form; keys are encrypted to disk and only decrypted for that user's JWT subject.

### Prerequisites

1. A public domain or tunnel pointing at your server (e.g. `https://imagine.your-domain.com`).
2. A DCR HMAC secret -- generate with `openssl rand -hex 32`.

### Required Env

| Variable | Description |
|:---------|:------------|
| `TRANSPORT_MODE=http` | Selects HTTP transport (multi-user). Equivalent: `MCP_TRANSPORT=http` or `--http` flag. |
| `PUBLIC_URL` | Public URL of your server (e.g. `https://imagine.your-domain.com`). Required to bind publicly. |
| `MCP_DCR_SERVER_SECRET` | HMAC secret for stateless Dynamic Client Registration. Generate via `openssl rand -hex 32`. |

Provider API keys (`GEMINI_API_KEY` / `OPENAI_API_KEY` / `XAI_API_KEY`) are **not** server env vars in HTTP mode -- each user pastes their own keys via the relay form on first connect.

### Run the Server

```bash
docker run -p 8080:8080 \
  -e TRANSPORT_MODE=http \
  -e PUBLIC_URL=https://imagine.your-domain.com \
  -e MCP_DCR_SERVER_SECRET=$(openssl rand -hex 32) \
  ghcr.io/n24q02m/imagine-mcp:latest
```

Point clients to your server:
```json
{
  "mcpServers": {
    "imagine": {
      "type": "http",
      "url": "https://imagine.your-domain.com/mcp"
    }
  }
}
```

On first connect, the client opens a browser to your relay form. Each user pastes the API keys they want available (any subset of Gemini / OpenAI / xAI), submits, and the keys are stored encrypted under that user's JWT subject. Subsequent connections from the same user reuse the saved keys.

## Method 6: Build from Source

1. Clone and install:
   ```bash
   git clone https://github.com/n24q02m/imagine-mcp.git
   cd imagine-mcp
   uv sync --group dev
   ```

2. Run the dev server (stdio):
   ```bash
   GEMINI_API_KEY="AIza..." uv run imagine-mcp
   ```

3. For HTTP mode (self-host):
   ```bash
   TRANSPORT_MODE=http \
   PUBLIC_URL=http://localhost:8080 \
   MCP_DCR_SERVER_SECRET=$(openssl rand -hex 32) \
   uv run imagine-mcp --http
   ```

## Test

Once configured, call from your MCP client:

```
understand(
  media_urls=["https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/300px-Cat_November_2010-1a.jpg"],
  prompt="What animal is this?",
  provider="gemini",
  tier="poor"
)
```

Expected: `{"text": "This is a cat...", "model": "gemini-3.1-flash-lite-preview", ...}`

## Environment Variable Reference

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `GEMINI_API_KEY` | At least one | -- | Google AI Studio (Gemini) API key. Stdio mode requires >=1 of the 3 provider keys. |
| `OPENAI_API_KEY` | At least one | -- | OpenAI API key (GPT-5.4 understanding + gpt-image generation). |
| `XAI_API_KEY` | At least one | -- | xAI (Grok) API key (Grok 4.20 understanding + Aurora generation). |
| `TRANSPORT_MODE` | No | `stdio` | Set to `http` for HTTP transport (multi-user paste-token). |
| `MCP_TRANSPORT` | No | -- | Equivalent to `TRANSPORT_MODE` (alias for parity). |
| `PUBLIC_URL` | Yes (http) | -- | Server's public URL for HTTP self-host. |
| `MCP_DCR_SERVER_SECRET` | Yes (http) | -- | HMAC secret for stateless Dynamic Client Registration. |

## Troubleshooting

### "No provider API keys set" / server exits immediately (stdio)

Stdio mode requires at least one of `GEMINI_API_KEY` / `OPENAI_API_KEY` / `XAI_API_KEY`. Set one in the plugin `env` block, or switch to HTTP mode (Method 5) for browser-based setup.

### `CredentialMissingError` on a specific provider call

You called `understand` / `generate` with a provider whose API key is not set. Either set that provider's key, or pass a different `provider=` argument (e.g. `provider="gemini"` if only Gemini key is set).

### `ProviderUnsupportedError` on video understanding / generation

OpenAI does not support video understanding or generation. xAI does not support video understanding. Use `provider="gemini"` for video paths -- see the capability matrix in [CLAUDE.md](../CLAUDE.md).

### Rate limit / quota errors

Try a different `provider=` argument, or wait and retry. Free Gemini tier is the most permissive for prototyping.

### uvx: old version or "command not found"

- Verify `uv` is installed: `uv --version`.
- Force latest: `uvx imagine-mcp@latest`.
- Clear the uv tool cache: `uv tool uninstall imagine-mcp && uvx imagine-mcp`.

### HTTP self-host: OAuth/relay form does not load

- Verify `PUBLIC_URL` matches the URL clients connect to.
- Verify `MCP_DCR_SERVER_SECRET` is set (server refuses to bind publicly without it).
- Check container logs for the relay setup URL on first request.
