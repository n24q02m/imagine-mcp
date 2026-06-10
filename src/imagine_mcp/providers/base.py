"""Provider protocol -- each provider module exposes 4 action functions."""

from __future__ import annotations

from typing import Any, Protocol


class ImagineProvider(Protocol):
    async def understand_image(
        self, url: str, prompt: str, tier: str, max_tokens: int = 2048
    ) -> dict[str, Any]: ...

    async def understand_video(
        self, url: str, prompt: str, tier: str, max_tokens: int = 2048
    ) -> dict[str, Any]: ...

    async def generate_image(
        self,
        prompt: str,
        tier: str,
        reference_image_url: str | None = None,
        aspect_ratio: str = "1:1",
    ) -> dict[str, Any]: ...

    async def generate_video(
        self,
        prompt: str,
        tier: str,
        reference_image_url: str | None = None,
        job_id: str | None = None,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
    ) -> dict[str, Any]: ...
