from __future__ import annotations

from datetime import date, timedelta

import pytest

from imagine_mcp.models import (
    MODELS,
    UNSUPPORTED,
    ModelEntry,
    default_provider_for,
    get_model_id,
    list_models,
    rank_for,
)


def test_gemini_understand_poor_rich() -> None:
    assert (
        get_model_id("gemini", "understand", "image", "poor")
        == "gemini-3.1-flash-lite-preview"
    )
    assert (
        get_model_id("gemini", "understand", "image", "rich")
        == "gemini-3.1-pro-preview"
    )
    assert (
        get_model_id("gemini", "understand", "video", "poor")
        == "gemini-3.1-flash-lite-preview"
    )


def test_gemini_generate_image_cross_gen() -> None:
    assert (
        get_model_id("gemini", "generate", "image", "poor")
        == "gemini-3.1-flash-image-preview"
    )
    assert (
        get_model_id("gemini", "generate", "image", "rich")
        == "gemini-3-pro-image-preview"
    )


def test_gemini_generate_video() -> None:
    assert (
        get_model_id("gemini", "generate", "video", "poor")
        == "veo-3.1-lite-generate-preview"
    )
    assert (
        get_model_id("gemini", "generate", "video", "rich")
        == "veo-3.1-generate-preview"
    )


def test_openai_understand_image() -> None:
    assert get_model_id("openai", "understand", "image", "poor") == "gpt-4o-mini"
    assert get_model_id("openai", "understand", "image", "rich") == "gpt-4o"


def test_openai_unsupported() -> None:
    assert get_model_id("openai", "understand", "video", "poor") is UNSUPPORTED
    assert get_model_id("openai", "generate", "video", "rich") is UNSUPPORTED


def test_grok_single_tier_video() -> None:
    assert get_model_id("grok", "generate", "video", "poor") == "grok-imagine-video"
    assert get_model_id("grok", "generate", "video", "rich") == "grok-imagine-video"


def test_grok_understand_unsupported_video() -> None:
    assert get_model_id("grok", "understand", "video", "poor") is UNSUPPORTED


def test_unknown_raises() -> None:
    with pytest.raises(KeyError):
        get_model_id("unknown", "understand", "image", "poor")


def test_rank_for_returns_int() -> None:
    r = rank_for("gemini", "generate", "image", "rich")
    assert isinstance(r, int)
    assert r >= 1


def test_rank_for_unsupported_is_none() -> None:
    assert rank_for("openai", "understand", "video", "poor") is None


def test_list_models_sorted_by_rank_within_group() -> None:
    group = list_models(
        filter_fn=lambda e: (
            e.action == "generate" and e.media == "image" and e.tier == "rich"
        ),
        sort_by="rank",
    )
    live_ranks = [e.quality_rank for e in group if e.model_id is not UNSUPPORTED]
    assert live_ranks == sorted(live_ranks)


def test_every_live_entry_has_rank_and_freshness() -> None:
    ninety_days_ago = date.today() - timedelta(days=90)
    for entry in MODELS:
        if entry.model_id is UNSUPPORTED:
            continue
        assert entry.quality_rank is not None and entry.quality_rank >= 1, (
            f"{entry}: quality_rank must be >= 1 for live entries"
        )
        assert entry.last_verified >= ninety_days_ago, (
            f"{entry}: last_verified {entry.last_verified} is stale (>90d). "
            "Run `mise run refresh-ranks`."
        )


def test_model_entry_shape() -> None:
    e = MODELS[0]
    assert isinstance(e, ModelEntry)
    keys = {(x.provider, x.action, x.media, x.tier) for x in MODELS}
    assert len(keys) == len(MODELS), "duplicate composite key in MODELS"


def test_default_provider_for_rank_1() -> None:
    # Gemini is rank 1 for generate.image.rich baseline
    assert default_provider_for("generate", "image", "rich") == "gemini"


def test_default_provider_fallback_when_only_unsupported() -> None:
    # openai has UNSUPPORTED for video understand; default_provider should fall back to gemini
    assert default_provider_for("understand", "video", "poor") == "gemini"
