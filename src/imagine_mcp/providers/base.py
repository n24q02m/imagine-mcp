"""Provider protocol and client management utilities."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol


class ImagineProvider(Protocol):
    """Gemini-only native methods (video/multimodal understand); generation
    is implemented by all three providers. Image understanding is uniformly
    handled by ``dispatcher._passthrough_understand`` (litellm) -- there is
    no per-provider ``understand_image`` (#461)."""

    async def understand_video(
        self, url: str, prompt: str, model: str, max_tokens: int = 2048
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


class ClientManager:
    """Manages provider client instances and API key resolution.

    Centralizes the logic for:
    1. Resolving API keys from per-subject credentials (HTTP multi-user) or
       environment variables/settings (single-user).
    2. Caching client instances per subject or globally.
    3. Raising CredentialMissingError with a consistent message.
    """

    def __init__(
        self,
        provider_name: str,
        env_key: str,
        settings_attr: str,
        client_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.env_key = env_key
        self.settings_attr = settings_attr
        self.client_factory = client_factory
        self._client: Any = None
        self._sub_clients: dict[str, Any] = {}

    def get_api_key(self) -> str:
        """Resolve the API key for the current request scope."""
        import os

        from imagine_mcp.config import settings
        from imagine_mcp.credential_state import (
            credentials_for_current_request,
            get_current_sub,
        )
        from imagine_mcp.errors import CredentialMissingError

        sub = get_current_sub()
        if sub is not None:
            key = credentials_for_current_request().get(self.env_key)
        else:
            key = getattr(settings, self.settings_attr) or os.environ.get(self.env_key)

        if not key:
            raise CredentialMissingError(
                f"{self.provider_name} API key missing. Run config(action='open_relay') for "
                f"browser-based setup, or set {self.env_key}."
            )
        return key

    def get_client(self) -> Any:
        """Return a (cached) client instance for the current request scope."""
        from imagine_mcp.credential_state import get_current_sub

        if self.client_factory is None:
            raise RuntimeError(f"No client_factory defined for {self.provider_name}")

        sub = get_current_sub()
        if sub is not None:
            cached = self._sub_clients.get(sub)
            if cached is not None:
                return cached
            client = self.client_factory(self.get_api_key())
            self._sub_clients[sub] = client
            return client

        if self._client is None:
            self._client = self.client_factory(self.get_api_key())
        return self._client

    def reset(self) -> None:
        """Clear all cached client instances."""
        self._client = None
        self._sub_clients.clear()
