# Imagine MCP -- Agent Setup Guide

> Give this file to your AI agent to automatically set up imagine-mcp.

> **2026-05-02 Update (v<auto>+)**: Plugin install (Option 1) now uses pure stdio mode with provider API key env vars.
> The previous "Zero-Config Relay" auto-spawn pattern has been removed.
> If you relied on the relay form to enter your keys, please:
> 1. Set at least one of `GEMINI_API_KEY` / `OPENAI_API_KEY` / `XAI_API_KEY` directly in plugin config (Option 1), OR
> 2. Switch to HTTP mode (self-host) for browser-based paste-token setup -- see `setup-manual.md` "Method 5".

## Option 1: Claude Code Plugin (Recommended)

Plugin marketplace install runs the server in **pure stdio mode** with provider env vars. No daemon-bridge, no auto-spawn, no relay form.

1. Get at least one provider API key:
   - **Google AI Studio** (Gemini): https://aistudio.google.com/apikey
   - **OpenAI**: https://platform.openai.com/api-keys
   - **xAI** (Grok): https://console.x.ai
2. Install the plugin:
   ```bash
   /plugin marketplace add n24q02m/claude-plugins
   /plugin install imagine-mcp@n24q02m-plugins
   ```
3. Set at least one of `GEMINI_API_KEY` / `OPENAI_API_KEY` / `XAI_API_KEY` in the plugin config (or your Claude Code settings). Any subset works.

This installs the server with skill: `/image-describe`.

## Option 2: MCP Direct (Stdio + uvx)

### Claude Code (settings.json)

Add to `.claude/settings.json` or `~/.claude/settings.json`:

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

### Codex CLI (config.toml)

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.imagine]
command = "uvx"
args = ["imagine-mcp"]

[mcp_servers.imagine.env]
GEMINI_API_KEY = "AIza..."
OPENAI_API_KEY = "sk-..."
XAI_API_KEY = "xai-..."
```

### OpenCode (opencode.json)

Add to `opencode.json` in your project root:

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

Supply only the keys you have -- any subset works.

## Option 3: Docker (Stdio)

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

Set the keys in your shell profile or pass them inline.

## Why upgrade to HTTP mode?

Stdio is the default and works fine for single-user local setups. You may want to switch to HTTP self-host mode when you need any of the following:

- **claude.ai web compatibility** -- claude.ai (the web UI) supports HTTP MCP servers but cannot spawn local stdio processes.
- **One server shared across N Claude Code sessions** -- a single HTTP instance serves multiple terminals/IDEs without re-spawning per session.
- **Browser-based paste-token setup** -- enter API keys in a relay form rather than editing JSON config; keys saved encrypted on disk per JWT subject.
- **Multi-device credential sync** -- save keys once, the same self-hosted server serves your desktop / tablet without re-entering.
- **Multi-user team sharing** -- a self-hosted server can serve multiple users, each with their own isolated set of provider keys (per-JWT-sub).
- **Always-on persistent process for webhooks/agents** -- HTTP servers stay alive between sessions, enabling background work, scheduled agents, or webhook listeners.

## Option 4: HTTP Self-Host (Multi-User Paste-Token)

Imagine MCP does **not** offer an n24q02m-hosted public instance -- provider API keys are paid per-token. Run your own:

```bash
docker run -p 8080:8080 \
  -e TRANSPORT_MODE=http \
  -e PUBLIC_URL=https://imagine.your-domain.com \
  -e MCP_DCR_SERVER_SECRET=$(openssl rand -hex 32) \
  ghcr.io/n24q02m/imagine-mcp:latest
```

Then point clients at your server:

### Claude Code (settings.json)

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

### Codex CLI (config.toml)

```toml
[mcp_servers.imagine]
type = "http"
url = "https://imagine.your-domain.com/mcp"
```

### OpenCode (opencode.json)

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

On first use, a browser window opens to the relay form. Each user pastes the API keys they want (any subset of Gemini / OpenAI / xAI), submits, and the keys are stored encrypted under that user's JWT subject.

For full self-host setup details (TLS, tunnel, env reference), see [setup-manual.md](setup-manual.md) "Method 5: Self-Hosting HTTP Mode".

## Environment Variables

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `GEMINI_API_KEY` | At least one (stdio) | -- | Google AI Studio (Gemini) API key. |
| `OPENAI_API_KEY` | At least one (stdio) | -- | OpenAI API key. |
| `XAI_API_KEY` | At least one (stdio) | -- | xAI (Grok) API key. |
| `TRANSPORT_MODE` | No | `stdio` | Set to `http` for multi-user paste-token mode. |
| `MCP_TRANSPORT` | No | -- | Equivalent to `TRANSPORT_MODE`. |
| `PUBLIC_URL` | Yes (http) | -- | Server's public URL for HTTP self-host. |
| `MCP_DCR_SERVER_SECRET` | Yes (http) | -- | HMAC secret for stateless client registration. |

## Authentication

### Stdio Mode (Provider API Keys)

Get at least one of:
- **Gemini**: https://aistudio.google.com/apikey -- key starts with `AIza`
- **OpenAI**: https://platform.openai.com/api-keys -- key starts with `sk-`
- **xAI**: https://console.x.ai -- key starts with `xai-`

Any subset is fine -- providers without a key surface `CredentialMissingError` only when called.

### HTTP Self-Host Mode (Paste-Token Relay)

No env-var keys on the server. Each user pastes their own provider API keys via the relay form on first connect; keys are encrypted to disk per JWT subject.

## Verification

After setup, verify the server is working:

```
Use the understand tool with a sample image URL and prompt to verify the server is connected and at least one provider key is configured.
```

Example call:
```
understand(
  media_urls=["https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/300px-Cat_November_2010-1a.jpg"],
  prompt="What animal is this?",
  provider="gemini",
  tier="poor"
)
```

Expected: a JSON dict with `text` describing a cat and `model` naming a Gemini model ID.
