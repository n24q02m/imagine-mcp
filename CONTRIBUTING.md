# Contributing to imagine-mcp

Thank you for your interest in contributing!

## Getting started

### Prerequisites

- [mise](https://mise.jdx.dev/) (recommended) or **Python 3.13+** and **uv**
- Git + a GitHub account

### Setup development environment

1. Fork and clone:

```bash
git clone https://github.com/YOUR_USERNAME/imagine-mcp
cd imagine-mcp
```

2. Install tools and dependencies:

```bash
mise run setup
```

Without mise:

```bash
uv sync --group dev
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

## Development workflow

### Run locally

```bash
mise run dev                  # http local relay mode (--http)
uv run imagine-mcp            # stdio mode (default, no flag)

# Optional: set env vars so the server skips the relay form
export GEMINI_API_KEY=...
export OPENAI_API_KEY=...
export XAI_API_KEY=...
```

### Make changes

1. Create a branch: `git checkout -b feature/your-feature-name`
2. Edit code, docs, or tests.
3. Run checks:

```bash
mise run lint                 # ruff + ruff format + ty
mise run test                 # fast unit tests (mocked)
mise run test -- -m live      # live tests (requires API keys)
```

4. Commit (pre-commit hooks will run gitleaks, ruff, ty, pytest).
5. Push + open a Pull Request.

## Commit convention

We use `python-semantic-release` v10 to auto-version releases from commits.

**Allowed prefixes**: `fix:` (patch) and `feat:` (minor). `chore(release):` is reserved for PSR.

**NOT allowed**: `refactor:`, `chore:` (except release), `docs:`, `ci:`, `build:`, `style:`, `perf:`, `test:`, or the `!` breaking-change marker.

Breaking changes: open an issue first to discuss the major version bump.

## Release process

Releases are automated via python-semantic-release v10 + `.github/workflows/cd.yml`.

1. Merge PRs into `main`.
2. A maintainer dispatches CD via `workflow_dispatch` and picks `beta` or `stable`.
3. PSR bumps version, updates CHANGELOG + version files, creates the tag.
4. CD publishes to PyPI (trusted publisher), builds multi-arch Docker images (DockerHub + ghcr.io), publishes to the MCP Registry (stable only), and syncs to the Claude Plugin Marketplace.

You do **not** need to create manual tags or changelog entries.

## Pull request checklist

- [ ] Single logical change, atomic commits.
- [ ] CI green (lint + tests on ubuntu + windows + macos).
- [ ] Commit messages follow `fix:` or `feat:` prefix.
- [ ] Documentation updated (`docs/*.md`, README) when user-facing behavior changes.
- [ ] Tests added or updated for the change.
- [ ] `SECURITY.md` followed for vulnerability disclosure.

## Code style

- Python 3.13, type hints required (enforced by `ty`).
- `ruff` handles lint + format (`mise run fix` to auto-apply).
- English for docstrings, comments, and commit messages (public repo).
- No emojis in code or documentation.

## Testing

```bash
uv run pytest                 # all non-live tests
uv run pytest -v              # verbose
uv run pytest -m security     # SSRF / path-traversal / injection boundary tests
```

Coverage target: 94% for v1.1 (fixtures covering real provider responses). v1.0 baseline is 48%; gate currently set to `fail_under = 45` in `pyproject.toml`.

## Project structure

```text
imagine-mcp/
|- src/imagine_mcp/
|   |- __init__.py
|   |- __main__.py         # Entry: dispatches stdio proxy vs http local relay
|   |- server.py           # FastMCP server, 4 tools (N+2 layout)
|   |- dispatcher.py       # Validates inputs, routes to provider
|   |- providers/          # gemini / openai / grok adapters
|   |- config.py           # Pydantic Settings
|   |- relay_schema.py     # Relay form fields
|   |- relay_setup.py      # ensure_config via mcp-core
|   |- cache.py            # diskcache wrapper
|   |- media.py            # URL -> image|video detection + download
|   `- docs/               # Tool documentation (Markdown)
|- scripts/                # CF deploy + dev tooling
|- tests/
|- pyproject.toml
|- server.json             # MCP Registry manifest
|- .claude-plugin/
|   `- plugin.json         # Claude Code plugin manifest
`- README.md
```

## Questions?

Open an issue for bug reports, feature requests, or architecture discussions. For security vulnerabilities see `SECURITY.md`.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
