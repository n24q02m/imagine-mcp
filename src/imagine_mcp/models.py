"""ModelEntry source of truth: provider x action x media x tier -> model_id + quality_rank.

Quality rank derived from Artificial Analysis + LMArena leaderboards via
scripts/fetch_leaderboards.py. UNSUPPORTED combos use rank=None.

Cross-gen exceptions documented inline - provider release reality, not design choice.
Verified 2026-04-18 from official docs; rank baseline 2026-04-24 from manual review
(automated refresh via weekly GH Action cron - see spec Section 15).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Final, Literal


class _Unsupported:
    """Sentinel for unsupported provider x media x action combos."""

    def __repr__(self) -> str:
        return "UNSUPPORTED"

    def __bool__(self) -> bool:
        return False


UNSUPPORTED: Final = _Unsupported()

Provider = Literal["gemini", "openai", "grok"]
Action = Literal["understand", "generate"]
Media = Literal["image", "video"]
Tier = Literal["poor", "rich"]
CostTier = Literal["low", "medium", "high"]

_BASELINE_DATE = date(2026, 4, 24)


@dataclass(frozen=True, slots=True)
class ModelEntry:
    provider: Provider
    action: Action
    media: Media
    tier: Tier
    model_id: str | _Unsupported
    quality_rank: int | None
    cost_tier: CostTier
    last_verified: date
    sources: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


MODELS: Final[list[ModelEntry]] = [
    # ----- understand.image -----
    ModelEntry(
        "gemini",
        "understand",
        "image",
        "poor",
        "gemini-3.1-flash-lite-preview",
        quality_rank=1,
        cost_tier="low",
        last_verified=_BASELINE_DATE,
        sources=("arena.ai/leaderboard/vision",),
    ),
    ModelEntry(
        "openai",
        "understand",
        "image",
        "poor",
        "gpt-5.4-mini",
        quality_rank=2,
        cost_tier="low",
        last_verified=_BASELINE_DATE,
        sources=("arena.ai/leaderboard/vision",),
    ),
    ModelEntry(
        "grok",
        "understand",
        "image",
        "poor",
        "grok-4.20-0309-non-reasoning",
        quality_rank=3,
        cost_tier="low",
        last_verified=_BASELINE_DATE,
        sources=("arena.ai/leaderboard/vision",),
    ),
    ModelEntry(
        "gemini",
        "understand",
        "image",
        "rich",
        "gemini-3.1-pro-preview",
        quality_rank=1,
        cost_tier="high",
        last_verified=_BASELINE_DATE,
        sources=("arena.ai/leaderboard/vision",),
    ),
    ModelEntry(
        "openai",
        "understand",
        "image",
        "rich",
        "gpt-5.4",
        quality_rank=2,
        cost_tier="high",
        last_verified=_BASELINE_DATE,
        sources=("arena.ai/leaderboard/vision",),
    ),
    ModelEntry(
        "grok",
        "understand",
        "image",
        "rich",
        "grok-4.20-0309-reasoning",
        quality_rank=3,
        cost_tier="high",
        last_verified=_BASELINE_DATE,
        sources=("arena.ai/leaderboard/vision",),
    ),
    # ----- understand.video (Gemini only) -----
    ModelEntry(
        "gemini",
        "understand",
        "video",
        "poor",
        "gemini-3.1-flash-lite-preview",
        quality_rank=1,
        cost_tier="low",
        last_verified=_BASELINE_DATE,
        notes="Native multimodal; no dedicated video leaderboard.",
    ),
    ModelEntry(
        "openai",
        "understand",
        "video",
        "poor",
        UNSUPPORTED,
        quality_rank=None,
        cost_tier="low",
        last_verified=_BASELINE_DATE,
        notes="GPT-5.4 image-only; extract frames or use gemini.",
    ),
    ModelEntry(
        "grok",
        "understand",
        "video",
        "poor",
        UNSUPPORTED,
        quality_rank=None,
        cost_tier="low",
        last_verified=_BASELINE_DATE,
        notes="Prod 4.20-0309-v2 image-only.",
    ),
    ModelEntry(
        "gemini",
        "understand",
        "video",
        "rich",
        "gemini-3.1-pro-preview",
        quality_rank=1,
        cost_tier="high",
        last_verified=_BASELINE_DATE,
    ),
    ModelEntry(
        "openai",
        "understand",
        "video",
        "rich",
        UNSUPPORTED,
        quality_rank=None,
        cost_tier="high",
        last_verified=_BASELINE_DATE,
    ),
    ModelEntry(
        "grok",
        "understand",
        "video",
        "rich",
        UNSUPPORTED,
        quality_rank=None,
        cost_tier="high",
        last_verified=_BASELINE_DATE,
    ),
    # ----- generate.image -----
    ModelEntry(
        "gemini",
        "generate",
        "image",
        "poor",
        "gemini-3.1-flash-image-preview",
        quality_rank=1,
        cost_tier="low",
        last_verified=_BASELINE_DATE,
        sources=(
            "artificialanalysis.ai/image/leaderboard/text-to-image",
            "arena.ai/leaderboard/text-to-image",
        ),
        notes="Nano Banana 2.",
    ),
    ModelEntry(
        "openai",
        "generate",
        "image",
        "poor",
        "gpt-image-1-mini",
        quality_rank=2,
        cost_tier="low",
        last_verified=_BASELINE_DATE,
        sources=("artificialanalysis.ai/image/leaderboard/text-to-image",),
    ),
    ModelEntry(
        "grok",
        "generate",
        "image",
        "poor",
        "grok-imagine-image",
        quality_rank=3,
        cost_tier="low",
        last_verified=_BASELINE_DATE,
        sources=(
            "artificialanalysis.ai/image/leaderboard/text-to-image",
            "arena.ai/leaderboard/text-to-image",
        ),
        notes="Aurora.",
    ),
    ModelEntry(
        "gemini",
        "generate",
        "image",
        "rich",
        "gemini-3-pro-image-preview",
        quality_rank=1,
        cost_tier="high",
        last_verified=_BASELINE_DATE,
        sources=(
            "artificialanalysis.ai/image/leaderboard/text-to-image",
            "arena.ai/leaderboard/text-to-image",
        ),
        notes="Nano Banana Pro. Cross-gen: no 3.1-pro-image as of 2026-04-18.",
    ),
    ModelEntry(
        "openai",
        "generate",
        "image",
        "rich",
        "gpt-image-1.5",
        quality_rank=2,
        cost_tier="high",
        last_verified=_BASELINE_DATE,
        notes="Cross-gen: no gpt-image-1.5-mini yet.",
    ),
    ModelEntry(
        "grok",
        "generate",
        "image",
        "rich",
        "grok-imagine-image-pro",
        quality_rank=3,
        cost_tier="high",
        last_verified=_BASELINE_DATE,
    ),
    # ----- generate.video -----
    ModelEntry(
        "gemini",
        "generate",
        "video",
        "poor",
        "veo-3.1-lite-generate-preview",
        quality_rank=1,
        cost_tier="low",
        last_verified=_BASELINE_DATE,
        sources=(
            "artificialanalysis.ai/video/leaderboard/text-to-video",
            "arena.ai/leaderboard/text-to-video",
        ),
    ),
    ModelEntry(
        "grok",
        "generate",
        "video",
        "poor",
        "grok-imagine-video",
        quality_rank=2,
        cost_tier="medium",
        last_verified=_BASELINE_DATE,
        notes="Single tier -- same model for poor and rich.",
    ),
    ModelEntry(
        "openai",
        "generate",
        "video",
        "poor",
        UNSUPPORTED,
        quality_rank=None,
        cost_tier="low",
        last_verified=_BASELINE_DATE,
        notes="Sora 2 API shutdown 2026-09-24.",
    ),
    ModelEntry(
        "gemini",
        "generate",
        "video",
        "rich",
        "veo-3.1-generate-preview",
        quality_rank=1,
        cost_tier="high",
        last_verified=_BASELINE_DATE,
        sources=(
            "artificialanalysis.ai/video/leaderboard/text-to-video",
            "arena.ai/leaderboard/text-to-video",
        ),
    ),
    ModelEntry(
        "grok",
        "generate",
        "video",
        "rich",
        "grok-imagine-video",
        quality_rank=2,
        cost_tier="medium",
        last_verified=_BASELINE_DATE,
    ),
    ModelEntry(
        "openai",
        "generate",
        "video",
        "rich",
        UNSUPPORTED,
        quality_rank=None,
        cost_tier="high",
        last_verified=_BASELINE_DATE,
    ),
]


# O(1) dictionary cache for fast model lookups, replacing O(n) list traversal.
_MODEL_CACHE: Final[dict[tuple[str, str, str, str], ModelEntry]] = {
    (e.provider, e.action, e.media, e.tier): e for e in MODELS
}

def _lookup(provider: str, action: str, media: str, tier: str) -> ModelEntry:
    try:
        return _MODEL_CACHE[(provider, action, media, tier)]
    except KeyError:
        raise KeyError(
            f"unknown combo: provider={provider!r} action={action!r} "
            f"media={media!r} tier={tier!r}"
        ) from None


def get_model_id(
    provider: str, action: str, media_type: str, tier: str
) -> str | _Unsupported:
    """Return model ID for a given combo.

    Raises KeyError if (provider, action, media, tier) not registered.
    Returns UNSUPPORTED sentinel if combo is registered but unsupported.
    """
    return _lookup(provider, action, media_type, tier).model_id


def rank_for(provider: str, action: str, media: str, tier: str) -> int | None:
    """Return quality_rank for a combo, or None if unsupported."""
    return _lookup(provider, action, media, tier).quality_rank


def list_models(
    filter_fn: Callable[[ModelEntry], bool] | None = None,
    sort_by: Literal["rank", "provider", "cost"] = "rank",
) -> list[ModelEntry]:
    """Return filtered + sorted copy of MODELS.

    sort_by="rank" sorts by (action, media, tier, quality_rank asc; None last).
    """
    rows = [e for e in MODELS if (filter_fn is None or filter_fn(e))]
    if sort_by == "rank":
        rows.sort(
            key=lambda e: (
                e.action,
                e.media,
                e.tier,
                e.quality_rank if e.quality_rank is not None else 10**9,
            )
        )
    elif sort_by == "provider":
        rows.sort(key=lambda e: (e.action, e.media, e.tier, e.provider))
    elif sort_by == "cost":
        cost_order = {"low": 0, "medium": 1, "high": 2}
        rows.sort(key=lambda e: (e.action, e.media, e.tier, cost_order[e.cost_tier]))
    return rows


def default_provider_for(action: str, media: str, tier: str) -> str:
    """Pick provider with rank 1 for (action, media, tier).

    Fallback 'gemini' if all unranked.
    """
    candidates = list_models(
        filter_fn=lambda e: (
            e.action == action
            and e.media == media
            and e.tier == tier
            and e.model_id is not UNSUPPORTED
        ),
        sort_by="rank",
    )
    if candidates and candidates[0].quality_rank is not None:
        return candidates[0].provider
    return "gemini"
