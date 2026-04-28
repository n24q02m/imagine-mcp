# Manual setup

## 1. Install

```bash
# Recommended: uvx
uvx imagine-mcp

# Or add to your MCP client config
{
  "mcpServers": {
    "imagine": {
      "command": "uvx",
      "args": ["imagine-mcp"]
    }
  }
}
```

Supported clients: Claude Desktop, Claude Code, Cursor, Windsurf, Copilot CLI, OpenCode, Antigravity, Gemini CLI, Amp.

## 2. Get API keys

At least one is required. Server runs in degraded mode with zero keys.

- **Google AI Studio**: https://aistudio.google.com/apikey (for Gemini)
- **OpenAI**: https://platform.openai.com/api-keys
- **xAI**: https://console.x.ai (for Grok)

## 3. Configure credentials

### Option A: Environment variables

Set in your MCP client config:

```json
{
  "mcpServers": {
    "imagine": {
      "command": "uvx",
      "args": ["imagine-mcp"],
      "env": {
        "GEMINI_API_KEY": "...",
        "OPENAI_API_KEY": "...",
        "XAI_API_KEY": "..."
      }
    }
  }
}
```

### Option B: Browser relay (recommended)

Call from your MCP client:

```
config(action="open_relay")
```

Server opens browser with a form. Paste your keys, submit. They're encrypted and saved to machine-bound storage (`config.enc`).

Verify:

```
config(action="status")
```

## 4. Test

```
understand(
  media_urls=["https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/300px-Cat_November_2010-1a.jpg"],
  prompt="What animal is this?",
  provider="gemini",
  tier="poor"
)
```

Expected: `{"text": "This is a cat...", "model": "gemini-3.1-flash-lite-preview", ...}`

## Troubleshooting

- **"CredentialMissingError"**: Run `config(action="open_relay")` or set env vars.
- **"ProviderUnsupportedError"**: See capability matrix in [CLAUDE.md](../CLAUDE.md).
- **Relay URL won't open**: Check stderr for the URL, open manually.
- **Rate limit**: Try a different `provider` parameter.
