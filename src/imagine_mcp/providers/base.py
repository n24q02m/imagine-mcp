"""Provider protocol -- each provider module exposes 4 action functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ImageParams:
    """Parameters for image generation."""

    prompt: str
    tier: str
    reference_image_url: str | None = None
    aspect_ratio: str = "1:1"


@dataclass(frozen=True, slots=True)
class VideoParams:
    """Parameters for video generation (async polling)."""

    prompt: str
    tier: str
    reference_image_url: str | None = None
    job_id: str | None = None
    aspect_ratio: str = "16:9"
    duration_seconds: int = 8


class ImagineProvider(Protocol):
    def understand_image(
        self, url: str, prompt: str, tier: str, max_tokens: int = 2048
    ) -> dict[str, Any]: ...

    def understand_video(
        self, url: str, prompt: str, tier: str, max_tokens: int = 2048
    ) -> dict[str, Any]: ...

    def generate_image(self, params: ImageParams) -> dict[str, Any]: ...

    def generate_video(self, params: VideoParams) -> dict[str, Any]: ...
