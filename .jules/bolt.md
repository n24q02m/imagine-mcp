## 2024-05-18 - Optimize default_provider_for lookups
**Learning:** `default_provider_for` in `src/imagine_mcp/models.py` performs an O(N log N) filtering and sorting of `MODELS` on every call. Since the parameter space (`action`, `media`, `tier`) is very small and bounded, caching the result yields a ~25x performance improvement. Standard lru_cache works perfectly for this use case.
**Action:** Use `@functools.lru_cache(maxsize=32)` to optimize functions that perform expensive queries or sorting over static lists when their parameter space is small and bounded.

## 2026-04-24 - OpenAI Image Edit Implementation
**Learning:** OpenAI's `images.edit` endpoint currently only supports the `dall-e-2` model; `dall-e-3` and newer models do not support inpainting/editing via this specific API. Additionally, the input image must be a square PNG with an alpha channel (RGBA).
**Action:** When implementing image editing for OpenAI, pin the model to `dall-e-2` and use Pillow to pre-process the reference image (convert to RGBA and resize to square, e.g., 1024x1024) to ensure API compatibility.
