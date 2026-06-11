"""Config schema for the relay setup page.

ONE model-chain task: ``understand`` (order = litellm fallback chain). The
three provider key fields are *derived* — they surface automatically for the
providers the chosen understand models use, and the SAME keys also drive the
native ``generate`` path (provider/tier catalog).
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
            "priority": "native (provider/tier catalog)",
            "description": (
                "Generation stays native and uses the SAME provider keys above "
                "(no model chain): Gemini image + Veo video, OpenAI image, "
                "Grok image/video. Provider auto-fallback XAI > OpenAI > Gemini."
            ),
        },
    ],
}
