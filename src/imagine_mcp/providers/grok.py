"""Grok (xAI) provider — all paths stubbed (plan riêng khi impl)."""
from __future__ import annotations
from typing import Any


def understand(tier: str, image_url: str, prompt: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: Grok grok-3-vision")


def generate(tier: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
    raise NotImplementedError("TODO: xAI flux-schnell / flux-pro")


def edit(tier: str, image_url: str, prompt: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: Grok image edit")


def video_status(tier: str, job_id: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: Grok video status")
