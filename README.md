# imagine-mcp

**Production-grade MCP server for image/video understanding and generation across Gemini, OpenAI, and Grok.**

[![CI](https://github.com/n24q02m/imagine-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/n24q02m/imagine-mcp/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/n24q02m/imagine-mcp/graph/badge.svg)](https://codecov.io/gh/n24q02m/imagine-mcp)
[![PyPI](https://img.shields.io/pypi/v/imagine-mcp.svg)](https://pypi.org/project/imagine-mcp/)
[![License](https://img.shields.io/github/license/n24q02m/imagine-mcp.svg)](https://github.com/n24q02m/imagine-mcp/blob/main/LICENSE)

[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-1.x-purple.svg)](https://github.com/modelcontextprotocol/python-sdk)
[![semantic-release](https://img.shields.io/badge/semantic--release-python-e10079.svg)](https://github.com/python-semantic-release/python-semantic-release)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen.svg)](https://docs.renovatebot.com)

<!-- mcp-name: io.github.n24q02m/imagine-mcp -->

## Features

- **4 MCP tools**: `understand`, `generate`, `config`, `help`
- **3 providers**: Google Gemini, OpenAI, xAI Grok — same interface, switch via param
- **2 tiers**: `poor` (cheap/fast) and `rich` (high quality) per provider
- **Image + video**: understanding (Gemini native multimodal) and generation
- **Zero-config onboarding**: browser-based credential setup via relay (no `.env`)
- **Degraded mode**: server starts with 0 credentials; configure via `config` tool
- **Cache**: automatic caching of understand responses (configurable TTL)
- **Leaderboard-ranked models**: provider ordering auto-refreshed weekly from Artificial Analysis + LMArena

## Quick start

```bash
# With uvx
uvx imagine-mcp

# Or via MCP client config (Claude Desktop / Cursor / etc.)
{
  "mcpServers": {
    "imagine": {
      "command": "uvx",
      "args": ["imagine-mcp"]
    }
  }
}
```

On first run, open the relay URL from stderr and submit your API keys.

See [docs/setup-with-agent.md](docs/setup-with-agent.md) and [docs/setup-manual.md](docs/setup-manual.md) for onboarding details.

## Model IDs

See [docs/models.md](docs/models.md) (auto-generated, leaderboard-sorted) and [CLAUDE.md](CLAUDE.md) for the full provider × action × tier → model ID mapping.

## Development

```bash
git clone https://github.com/n24q02m/imagine-mcp
cd imagine-mcp
mise run setup    # install tools, deps, pre-commit hooks
mise run test     # run test suite
mise run dev      # run server in dev mode
```

## License

MIT. See [LICENSE](LICENSE).
