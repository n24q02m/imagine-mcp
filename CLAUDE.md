# imagine-mcp

MCP server đa năng cho image/video understanding + generation (private repo).

## Architecture 2×2×3

- **Mode**: `understand` | `generate` (+ `edit` cho image, `video_status` polling)
- **Tier**: `poor` (cheap/fast) | `rich` (high quality)
- **Providers**: `gemini` | `openai` | `grok`

## Mega-tool

```python
imagine(
    action: "understand" | "generate" | "edit" | "video_status",
    provider: "gemini" | "openai" | "grok",
    tier: "poor" | "rich",
    **kwargs,
) -> dict
```

## Model IDs per provider (2026 reference — verify trước khi submit)

- Gemini understand: `gemini-3.1-flash` (poor), `gemini-3.1-pro` (rich)
- Gemini image gen: `imagen-3.0-fast-generate-001` (poor), `imagen-4.0-generate-001` (rich)
- Gemini video gen: `veo-3.1-generate`
- OpenAI understand: `gpt-4o-mini` (poor), `gpt-4o` (rich)
- OpenAI image gen: `dall-e-3` (poor), `gpt-image-1` (rich)
- OpenAI video gen: `sora-1.0`
- Grok understand: `grok-3-mini-vision` (poor), `grok-3-vision` (rich)
- Grok image gen: `flux-schnell` (poor), `flux-pro` (rich)

## Secrets (Doppler)

- `GOOGLE_AI_STUDIO_API_KEY` — reuse từ project `virtual-company`
- `OPENAI_API_KEY`
- `XAI_API_KEY`

## Scope hiện tại (scaffold 2026-04-17)

- Mega-tool dispatch + validation: DONE
- Gemini `understand` reference impl: DONE
- OpenAI/Grok providers: stubs (`NotImplementedError`)
- Generate/edit/video_status: stubs
- Live E2E test: BLOCKED pending `GOOGLE_AI_STUDIO_API_KEY` trong Doppler

Full 18-path implementation sẽ viết plan riêng qua `superpowers:writing-plans`.

## Commits

`fix:` hoặc `feat:` prefix only. Tiếng Việt cho tài liệu trong repo private.
