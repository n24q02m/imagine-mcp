# Style Guide - imagine-mcp

## Architecture
Image/video understanding and generation MCP server. Python 3.13, single-package repo, 4 tools (`understand`, `generate`, `config`, `help`) × 3 providers (Gemini, OpenAI, Grok) × 2 tiers (poor, rich).

## Python
- Formatter/Linter: Ruff (line-length 88, target py313)
- Type checker: ty (lenient config)
- Test: pytest + pytest-asyncio (asyncio_mode=auto)
- Package manager: uv
- SDK: mcp[cli] FastMCP
- Core deps: google-genai, openai, httpx, diskcache, n24q02m-mcp-core

## Code Patterns
- Async/await with `httpx.AsyncClient` for Grok REST calls
- SDK (`google-genai`, `openai`) for Gemini + OpenAI paths
- Dispatcher validates action/provider/tier, routes to provider module
- Provider module returns normalized `{"text"|"image_path"|"video_path", "model", "provider", "tier", "usage", ...}` dict
- `UNSUPPORTED` sentinel for provider × action × media combos with no API (openai video, grok video understand)
- Video generation is async: submit returns `job_id`, poll with `generate(media_type="video", job_id=...)`
- Cache layer (diskcache) for understand responses (TTL 3600s default)
- Reuse `n24q02m-mcp-core` primitives (credential state, config.enc, relay client, local relay server, browser open)

## Commits
Conventional Commits — **ONLY** `fix:` and `feat:` prefixes. `chore(release):` reserved for python-semantic-release.

## Security
- SSRF prevention: validate `media_urls` and `reference_image_url` via `mcp-core` URL validator or provider SDK
- No path traversal in `output_dir` (resolve + ensure under `platformdirs.user_cache_dir`)
- Prompt injection: wrap untrusted content in `<untrusted_user_content>` XML boundary
- Credentials never appear in error messages, logs, or telemetry
- Never raise exceptions from MCP tool bodies — return error strings `{"error": "..."}` or raise typed exceptions that the dispatcher serializes

## Leaderboard pipeline
- `scripts/fetch_leaderboards.py` parses Artificial Analysis + LMArena HTML tables
- `scripts/gen_models_table.py` renders `docs/models.md` from `src/imagine_mcp/models.py` (pre-commit drift check)
- GitHub Actions cron (`refresh-ranks.yml`) runs weekly (Monday 00:00 UTC), opens PR if ranks change
- `MODEL_ALIASES` dict maps leaderboard display names to canonical model IDs; update on alias drift
