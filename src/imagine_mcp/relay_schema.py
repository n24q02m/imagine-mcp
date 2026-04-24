"""Config schema for the relay setup page (3 optional API key fields)."""

from __future__ import annotations

from typing import Any

RELAY_SCHEMA: dict[str, Any] = {
    "server": "imagine-mcp",
    "displayName": "Imagine MCP",
    "description": (
        "Enter API keys for the providers you want to use. "
        "All fields are optional -- the server starts in degraded mode with no keys "
        "and individual providers fail with CredentialMissingError when called."
    ),
    "fields": [
        {
            "key": "GOOGLE_AI_STUDIO_API_KEY",
            "label": "Google AI Studio API Key",
            "type": "password",
            "placeholder": "AIza...",
            "helpUrl": "https://aistudio.google.com/apikey",
            "helpText": (
                "Gemini understand (image/video) + image/video generation. "
                "Free tier available."
            ),
            "required": False,
        },
        {
            "key": "OPENAI_API_KEY",
            "label": "OpenAI API Key",
            "type": "password",
            "placeholder": "sk-...",
            "helpUrl": "https://platform.openai.com/api-keys",
            "helpText": (
                "GPT-5.4 image understanding + gpt-image-1 generation. "
                "Video paths are not supported."
            ),
            "required": False,
        },
        {
            "key": "XAI_API_KEY",
            "label": "xAI (Grok) API Key",
            "type": "password",
            "placeholder": "xai-...",
            "helpUrl": "https://console.x.ai",
            "helpText": (
                "Grok 4.20 image understanding + Aurora/Grok Imagine generation. "
                "Video understanding is not supported."
            ),
            "required": False,
        },
    ],
    "capabilityInfo": [
        {
            "label": "Image understanding",
            "priority": "Gemini > OpenAI > Grok",
            "description": (
                "Multi-image vision QA. Gemini 3 Pro is native multimodal and "
                "handles video natively."
            ),
        },
        {
            "label": "Image generation",
            "priority": "Gemini > OpenAI > Grok",
            "description": (
                "Text-to-image and reference-image editing. "
                "Gemini (Nano Banana) leads leaderboards as of baseline."
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
            "label": "Video generation",
            "priority": "Gemini (Veo 3.1) > Grok (Imagine)",
            "description": (
                "Async generate: submit returns job_id, poll via "
                "generate(media_type='video', job_id=...)."
            ),
        },
    ],
}
