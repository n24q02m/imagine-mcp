"""OpenAI provider — all paths stubbed (plan riêng khi impl)."""
from __future__ import annotations
from typing import Any


def understand(tier: str, image_url: str, prompt: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: OpenAI gpt-4o vision")


def generate(tier: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
    raise NotImplementedError("TODO: OpenAI dall-e-3 / gpt-image-1")


def edit(tier: str, image_url: str, prompt: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: OpenAI image edit")


def video_status(tier: str, job_id: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: OpenAI Sora status")
