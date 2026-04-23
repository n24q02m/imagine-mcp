"""imagine-mcp server: mega-tool dispatcher for image/video across Gemini/OpenAI/Grok."""
from __future__ import annotations
from typing import Any

from .providers import gemini, grok, openai

_PROVIDERS: dict[str, Any] = {"gemini": gemini, "openai": openai, "grok": grok}
_ACTIONS = {"understand", "generate", "edit", "video_status"}
_TIERS = {"poor", "rich"}

_SORTED_PROVIDERS = sorted(_PROVIDERS)
_SORTED_ACTIONS = sorted(_ACTIONS)
_SORTED_TIERS = sorted(_TIERS)

_HELP_TEXT = (
    "imagine(action, provider, tier, **kwargs)\n"
    f"  action: {_SORTED_ACTIONS}\n"
    f"  provider: {_SORTED_PROVIDERS}\n"
    f"  tier: {_SORTED_TIERS}\n"
    "See CLAUDE.md for model IDs per provider+tier."
)


def dispatch(action: str, provider: str, tier: str = "poor", **kwargs: Any) -> dict:
    """Validate + route to provider-specific function.

    Raises ValueError cho unknown action/provider/tier.
    NotImplementedError bubbled up từ provider stubs cho unimplemented paths.
    """
    if action not in _ACTIONS:
        raise ValueError(f"Unknown action: {action!r}. Valid: {_SORTED_ACTIONS}")
    if provider not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {provider!r}. Valid: {_SORTED_PROVIDERS}")
    if tier not in _TIERS:
        raise ValueError(f"Unknown tier: {tier!r}. Valid: {_SORTED_TIERS}")
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
        return _HELP_TEXT

    @app.tool()
    def config(key: str | None = None) -> dict:
        """Return current config (providers available, actions, tiers)."""
        return {
            "providers": _SORTED_PROVIDERS,
            "actions": _SORTED_ACTIONS,
            "tiers": _SORTED_TIERS,
        }

    app.run()


if __name__ == "__main__":
    main()
