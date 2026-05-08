"""Provider protocol -- each provider module exposes 4 action functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from imagine_mcp.models import GenerateParams


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
        params: GenerateParams | None = None,
    ) -> dict[str, Any]: ...

    def generate_video(
        self,
        prompt: str,
        tier: str,
        params: GenerateParams | None = None,
    ) -> dict[str, Any]: ...
