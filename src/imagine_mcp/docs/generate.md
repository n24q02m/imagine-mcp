# generate tool

Generate an image or video from a text prompt (optionally with a reference image).

## Signature

```python
generate(
    media_type: "image" | "video",
    prompt: str,
    provider: str | None = None,  # auto-fallback when None
    tier: str = "poor",
    reference_image_url: str | None = None,
    job_id: str | None = None,
    output_mode: "base64" | "path" | "both" = "both",
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
) -> dict
```

## Auto-fallback provider

When ``provider`` is omitted (``None``), imagine resolves the first provider
whose API key is present in the environment, in priority order
``XAI_API_KEY`` -> ``OPENAI_API_KEY`` -> ``GEMINI_API_KEY``. Gemini is last
because Google AI Studio billing-locking can return 403 ``PERMISSION_DENIED``
without warning. If no key is configured the call raises
``CredentialMissingError`` listing the three env vars.

## Image generate

```python
generate(
    media_type="image",
    prompt="a watercolor painting of a fox at sunrise",
    provider="gemini",
    tier="rich",
    aspect_ratio="16:9",
)
```

## Image edit (reference_image_url)

```python
generate(
    media_type="image",
    prompt="add a hat to the fox",
    provider="openai",
    tier="rich",
    reference_image_url="https://example.com/fox.png",
)
```

## Video generate (async)

```python
# 1) Submit job
result = generate(
    media_type="video",
    prompt="a dog running through a park",
    provider="gemini",
    tier="rich",
    duration_seconds=8,
)
# -> {"job_id": "op-abc123", "status": "pending", "eta_seconds": 60, ...}

# 2) Poll with job_id
status = generate(
    media_type="video",
    job_id="op-abc123",
)
```

Sync timeout: 300 seconds. On timeout, resume by calling `generate(media_type="video", job_id=...)`.

## Model IDs per tier

See `docs/models.md` or `config(action="status")`.

## Errors

- `ProviderUnsupportedError` -- e.g. `openai + video` (Sora 2 shutdown), `grok + video understand`
- `CredentialMissingError` -- API key not configured
- `VideoJobTimeoutError` -- sync poll exceeded 300s (job still running; resume with `job_id`)
