"""Provider protocol -- each provider module exposes 4 action functions."""

from __future__ import annotations

from typing import Any, Protocol, TypedDict, Unpack


class GenerateOptions(TypedDict, total=False):
    """Optional parameters for image and video generation."""

    reference_image_url: str | None
    job_id: str | None
    aspect_ratio: str
    duration_seconds: int


class ImagineProvider(Protocol):
    def understand_image(
        self, url: str, prompt: str, tier: str, max_tokens: int = 2048
    ) -> dict[str, Any]: ...

    def understand_video(
        self, url: str, prompt: str, tier: str, max_tokens: int = 2048
    ) -> dict[str, Any]: ...

    def generate_image(
        self,
        prompt: str,
        tier: str,
        **kwargs: Unpack[GenerateOptions],
    ) -> dict[str, Any]: ...

    def generate_video(
        self,
        prompt: str,
        tier: str,
        **kwargs: Unpack[GenerateOptions],
    ) -> dict[str, Any]: ...
