"""Provider base types and shared utilities."""

from __future__ import annotations

import os
from typing import Any, Callable, Protocol

from imagine_mcp.errors import CredentialMissingError


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
        reference_image_url: str | None = None,
        aspect_ratio: str = "1:1",
    ) -> dict[str, Any]: ...

    def generate_video(
        self,
        prompt: str,
        tier: str,
        reference_image_url: str | None = None,
        job_id: str | None = None,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
    ) -> dict[str, Any]: ...


class ClientManager:
    """Manages API client lifecycle and credential resolution for a provider.

    Handles per-user client caching for multi-user mode and falls back to
    global settings/environment variables for single-user/stdio mode.
    """

    def __init__(
        self,
        provider_name: str,
        env_var: str,
        settings_attr: str,
        client_factory: Callable[[str], Any],
    ):
        self.provider_name = provider_name
        self.env_var = env_var
        self.settings_attr = settings_attr
        self.client_factory = client_factory
        self._client: Any = None
        self._sub_clients: dict[str, Any] = {}

    def get_api_key(self) -> str:
        """Resolve the API key for the current request scope."""
        from imagine_mcp.config import settings
        from imagine_mcp.credential_state import (
            credentials_for_current_request,
            get_current_sub,
        )

        sub = get_current_sub()
        if sub is not None:
            key = credentials_for_current_request().get(self.env_var)
        else:
            key = getattr(settings, self.settings_attr) or os.environ.get(self.env_var)

        if not key:
            raise CredentialMissingError(
                f"{self.provider_name} API key missing. Run config(action='open_relay') for "
                f"browser-based setup, or set {self.env_var}."
            )
        return key

    def get_client(self) -> Any:
        """Return a cached client instance for the current request scope."""
        from imagine_mcp.credential_state import get_current_sub

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
        """Clear all cached client instances (primarily for testing)."""
        self._client = None
        self._sub_clients.clear()
