"""Config schema for the relay setup page.

TWO model-chain tasks: ``understand`` (litellm fallback chain) and ``generate``
(native provider/model selection -- the first entry's prefix picks the provider
and its model segment overrides the catalog model_id). The three provider key
fields are *derived* — they surface automatically for the providers the chosen
models use, and the SAME keys drive both the understand and generate paths.
"""

from __future__ import annotations

from typing import Any

# Catalog understand IMAGE models, explicit ``provider/`` prefixes.
_UNDERSTAND_SUGGESTED = [
    "xai/grok-4.20-0309-non-reasoning",
    "xai/grok-4.20-0309-reasoning",
    "gemini/gemini-3.1-flash-lite-preview",
    "gemini/gemini-3.1-pro-preview",
    "openai/gpt-5.4-mini",
    "openai/gpt-5.4",
]

# Catalog generate models, explicit ``provider/`` prefixes. The first entry of
# a chosen GENERATE_MODELS chain selects the native provider + overrides the
# catalog model_id; leaving it empty keeps the provider/tier catalog default.
_GENERATE_SUGGESTED = [
    "gemini/gemini-3.1-flash-image-preview",
    "gemini/gemini-3-pro-image-preview",
    "gemini/veo-3.1-lite-generate-preview",
    "gemini/veo-3.1-generate-preview",
    "openai/gpt-image-1-mini",
    "openai/gpt-image-1.5",
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
            "suggestedModels": _UNDERSTAND_SUGGESTED,
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
