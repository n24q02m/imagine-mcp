"""Config schema for the relay setup page.

TWO model-chain tasks: ``understand`` (litellm fallback chain) and ``generate``
(native provider/model selection -- the first entry's prefix picks the provider
and its model segment overrides the catalog model_id). The three provider key
fields are *derived* — they surface automatically for the providers the chosen
models use, and the SAME keys drive both the understand and generate paths.
"""

from __future__ import annotations

from typing import Any

# UNDERSTAND models are fully catalog-driven: the litellm chat catalog covers
# the gemini/openai/xai vision models, so the dropdown carries no hardcoded
# suggestions (the user searches the real provider/model space).

# GENERATE keeps a MINIMAL supplement: only the native grok (xAI) image/video
# models, a verified litellm gap (absent from the generate catalog) with no
# keyless list endpoint to fetch. Gemini/OpenAI generation models come from the
# litellm generate catalog (image/video modes), not hardcode. The first entry of
# a chosen GENERATE_MODELS chain selects the native provider + overrides the
# catalog model_id; leaving it empty keeps the provider/tier catalog default.
_GENERATE_SUGGESTED = [
    "grok/grok-imagine-image",
    "grok/grok-imagine-image-pro",
    "grok/grok-imagine-video",
]


def _key_field(key: str, label: str, ph: str, url: str) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "type": "password",
        "placeholder": ph,
        "helpUrl": url,
        "derived": True,
        "required": False,
    }


RELAY_SCHEMA: dict[str, Any] = {
    "server": "imagine-mcp",
    "displayName": "Imagine MCP",
    "description": (
        "Pick understand models (order = fallback). Leave empty to use the "
        "provider/tier catalog default. Key fields appear automatically for "
        "the providers your models use — the same keys also power generation."
    ),
    "fields": [
        {
            "key": "UNDERSTAND_MODELS",
            "label": "Understand models",
            "type": "model-chain",
            "task": "understand",
            "hasLocal": False,
            "placeholder": "add understand model…",
        },
        {
            "key": "GENERATE_MODELS",
            "label": "Generate models",
            "type": "model-chain",
            "task": "generate",
            "suggestedModels": _GENERATE_SUGGESTED,
            "hasLocal": False,
            "placeholder": "add generate model…",
        },
        _key_field(
            "GEMINI_API_KEY",
            "Gemini API Key",
            "AIza...",
            "https://aistudio.google.com/apikey",
        ),
        _key_field(
            "OPENAI_API_KEY",
            "OpenAI API Key",
            "sk-...",
            "https://platform.openai.com/api-keys",
        ),
        _key_field(
            "XAI_API_KEY",
            "xAI (Grok) API Key",
            "xai-...",
            "https://console.x.ai",
        ),
    ],
    "capabilityInfo": [
        {
            "label": "Image understanding",
            "priority": "configurable",
            "description": (
                "Multi-image vision QA across Gemini / OpenAI / Grok via the "
                "UNDERSTAND_MODELS chain (order = fallback)."
            ),
        },
        {
            "label": "Video understanding",
            "priority": "Gemini only",
            "description": (
                "Gemini native multimodal supports video frames. "
                "OpenAI/Grok raise ProviderUnsupportedError."
            ),
        },
        {
            "label": "Image / video generation",
            "priority": "configurable (native)",
            "description": (
                "Generation stays native and uses the SAME provider keys above. "
                "Pick GENERATE_MODELS to choose a provider + model (first entry "
                "wins); leave empty to use the provider/tier catalog default. "
                "Gemini image + Veo video, OpenAI image, Grok image/video. "
                "Provider auto-fallback order XAI, OpenAI, Gemini "
                "(override via GENERATE_PROVIDER_PRIORITY)."
            ),
        },
    ],
}
