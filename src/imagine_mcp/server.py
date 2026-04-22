"""imagine-mcp server: mega-tool dispatcher for image/video across Gemini/OpenAI/Grok."""
from __future__ import annotations
from typing import Any

from .providers import gemini, grok, openai

_PROVIDERS: dict[str, Any] = {"gemini": gemini, "openai": openai, "grok": grok}
_ACTIONS = {"understand", "generate", "edit", "video_status"}
_TIERS = {"poor", "rich"}


def dispatch(action: str, provider: str, tier: str = "poor", **kwargs: Any) -> dict:
    """Validate + route to provider-specific function.

    Raises ValueError cho unknown action/provider/tier.
    NotImplementedError bubbled up từ provider stubs cho unimplemented paths.
    """
    if "image_url" in kwargs:
        from urllib.parse import urlparse
        parsed = urlparse(kwargs["image_url"])
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid image_url scheme: {parsed.scheme!r}. Must be 'http' or 'https'")

    if action not in _ACTIONS:
        raise ValueError(f"Unknown action: {action!r}. Valid: {sorted(_ACTIONS)}")
    if provider not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider: {provider!r}. Valid: {sorted(_PROVIDERS)}"
        )
    if tier not in _TIERS:
        raise ValueError(f"Unknown tier: {tier!r}. Valid: {sorted(_TIERS)}")
    mod = _PROVIDERS[provider]
    fn = getattr(mod, action, None)
    if fn is None:
        raise NotImplementedError(f"{provider}.{action} not implemented yet")
    return fn(tier=tier, **kwargs)


def main() -> None:
    """FastMCP entrypoint — exposes `imagine`, `help`, `config` tools."""
    from fastmcp import FastMCP

    app = FastMCP("imagine-mcp")

    @app.tool()
    def imagine(
        action: str, provider: str, tier: str = "poor", **kwargs: Any
    ) -> dict:
        """Mega-tool dispatch for image/video understanding and generation."""
        return dispatch(action=action, provider=provider, tier=tier, **kwargs)

    @app.tool()
    def help() -> str:
        """Return usage guide (see CLAUDE.md for full architecture)."""
        return (
            "imagine(action, provider, tier, **kwargs)\n"
            f"  action: {sorted(_ACTIONS)}\n"
            f"  provider: {sorted(_PROVIDERS)}\n"
            f"  tier: {sorted(_TIERS)}\n"
            "See CLAUDE.md for model IDs per provider+tier."
        )

    @app.tool()
    def config(key: str | None = None) -> dict:
        """Return current config (providers available, actions, tiers)."""
        return {
            "providers": sorted(_PROVIDERS),
            "actions": sorted(_ACTIONS),
            "tiers": sorted(_TIERS),
        }

    app.run()


if __name__ == "__main__":
    main()
