# understand tool

Understand images and/or videos via a multimodal LLM.

## Signature

```python
understand(
    media_urls: list[str],       # HTTP(S) URLs -- max 5
    prompt: str,                 # Your question or instruction
    provider: str = "gemini",    # "gemini" | "openai" | "grok"
    tier: str = "poor",          # "poor" | "rich"
    max_tokens: int = 2048,
) -> dict
```

## Returns

```json
{
  "text": "...",
  "model": "gemini-3.1-flash-lite-preview",
  "provider": "gemini",
  "tier": "poor",
  "multimodal": true
}
```

## Provider x Media capability

| | image | video |
|---|:---:|:---:|
| gemini | yes | yes (native multimodal, mixed OK) |
| openai | yes | no (GPT-5.4 image-only -- extract frames) |
| grok | yes | no (prod image-only; beta has video) |

## Example: single image

```python
understand(
    media_urls=["https://example.com/cat.png"],
    prompt="What breed is this cat?",
    provider="gemini",
    tier="rich",
)
```

## Example: mixed image + video (Gemini only)

```python
understand(
    media_urls=["https://example.com/cat.png", "https://example.com/dog.mp4"],
    prompt="Compare the subjects in these two files.",
    provider="gemini",
    tier="rich",
)
```

## Tier difference

- `poor`: cheapest/fastest
- `rich`: highest quality

See `docs/models.md` (or `help(topic="config")`) for the current leaderboard-ranked table.

## Errors

- `InvalidProviderError` -- provider not in {gemini, openai, grok}
- `InvalidTierError` -- tier not in {poor, rich}
- `ProviderUnsupportedError` -- provider does not support the media type
- `CredentialMissingError` -- API key not configured (run `config(action="open_relay")`)
- `RateLimitError` -- provider 429
