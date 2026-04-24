# Contributing to imagine-mcp

Thanks for your interest in contributing!

## Development setup

```bash
git clone https://github.com/n24q02m/imagine-mcp
cd imagine-mcp
mise run setup
```

This installs Python 3.13, uv, dependencies, and pre-commit hooks.

## Running tests

```bash
mise run test              # fast unit tests (mocked)
mise run test -- -m live   # live tests (requires API keys)
```

## Commit convention

We use `python-semantic-release` v10 to auto-version releases from commits.

**Allowed prefixes**: `fix:` (patch) and `feat:` (minor). `chore(release):` is reserved for PSR.

**NOT allowed**: `refactor:`, `chore:` (except release), `docs:`, `ci:`, `build:`, `style:`, `perf:`, `test:`, or `!` breaking-change marker.

Breaking changes: open an issue first to discuss major version bump.

## Pull request process

1. Fork + branch from `main`.
2. One logical change per PR (atomic commits).
3. Pre-commit hooks run on commit (`ruff`, `ty`, `pytest`).
4. CI must be green.
5. PR needs 1 approval + code owner review.
6. Squash merge only.

## Issue reporting

Use the issue templates at `.github/ISSUE_TEMPLATE/`. For security issues, see `SECURITY.md`.

## Code style

- Python 3.13, type hints required (`ty` checker).
- `ruff` format + lint (auto-fix via `mise run fix`).
- English for docstrings and comments (public repo).
- No emojis in code or documentation.

## Refreshing model ranks

Model ordering in `docs/models.md` is derived from Artificial Analysis + LMArena leaderboards. To update manually:

```bash
mise run refresh-ranks
```

A GitHub Actions workflow (`.github/workflows/refresh-ranks.yml`) runs the same command weekly (Monday 00:00 UTC) and opens a PR if ranks changed. When adding a new model alias (display name → canonical model ID), update `scripts/fetch_leaderboards.py::MODEL_ALIASES`.
