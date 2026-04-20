"""Gemini provider. Reference impl for `understand` mode (tier poor|rich)."""
from __future__ import annotations
import os
from typing import Any

_CLIENT = None

_MODELS: dict[str, dict[str, str]] = {
    "understand": {"poor": "gemini-3.1-flash", "rich": "gemini-3.1-pro"},
    "generate": {
        "poor": "imagen-3.0-fast-generate-001",
        "rich": "imagen-4.0-generate-001",
    },
    "video": {"poor": "veo-3.1-generate", "rich": "veo-3.1-generate"},
}


def _client():
    global _CLIENT
    if _CLIENT is None:
        from google import genai

        api_key = os.environ.get("GOOGLE_AI_STUDIO_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GOOGLE_AI_STUDIO_API_KEY missing — inject via Doppler "
                "(doppler run --project virtual-company --config dev -- ...)"
            )
        _CLIENT = genai.Client(api_key=api_key)
    return _CLIENT


def understand(tier: str, image_url: str, prompt: str) -> dict[str, Any]:
    """Image understanding via Gemini flash/pro. Accepts http(s) image URL."""
    if not (image_url.startswith("http://") or image_url.startswith("https://")):
        raise ValueError("Invalid image_url: must start with http:// or https://")

    from google.genai import types

    model = _MODELS["understand"][tier]
    resp = _client().models.generate_content(
        model=model,
        contents=[
            prompt,
            types.Part.from_uri(file_uri=image_url, mime_type="image/png"),
        ],
    )
    return {"text": resp.text, "model": model, "provider": "gemini"}


def generate(tier: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
    raise NotImplementedError("TODO: Gemini Imagen integration (plan riêng)")


def edit(tier: str, image_url: str, prompt: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: Gemini image edit (plan riêng)")


def video_status(tier: str, job_id: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: Veo video status polling (plan riêng)")
