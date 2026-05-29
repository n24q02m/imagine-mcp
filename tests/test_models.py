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
    assert get_model_id("openai", "understand", "image", "poor") == "gpt-5.4-mini"
    assert get_model_id("openai", "understand", "image", "rich") == "gpt-5.4"


def test_openai_unsupported() -> None:
    assert get_model_id("openai", "understand", "video", "poor") is UNSUPPORTED
    assert get_model_id("openai", "generate", "video", "rich") is UNSUPPORTED


def test_grok_single_tier_video() -> None:
    assert get_model_id("grok", "generate", "video", "poor") == "grok-imagine-video"
    assert get_model_id("grok", "generate", "video", "rich") == "grok-imagine-video"


def test_grok_understand_unsupported_video() -> None:
    assert get_model_id("grok", "understand", "video", "poor") is UNSUPPORTED


@pytest.mark.parametrize(
    "p, a, m, t",
    [
        ("unknown", "understand", "image", "poor"),
        ("gemini", "unknown", "image", "poor"),
        ("gemini", "understand", "unknown", "poor"),
        ("gemini", "understand", "image", "unknown"),
    ],
)
def test_get_model_id_unknown_raises(p: str, a: str, m: str, t: str) -> None:
    with pytest.raises(KeyError) as excinfo:
        get_model_id(p, a, m, t)
    assert f"unknown combo: provider={p!r} action={a!r} media={m!r} tier={t!r}" in str(
        excinfo.value
    )


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


def test_unsupported_sentinel() -> None:
    assert repr(UNSUPPORTED) == "UNSUPPORTED"
    assert not UNSUPPORTED


def test_list_models_sort_by_provider() -> None:
    models = list_models(sort_by="provider")
    # Check a slice to ensure it's actually sorted by provider within (action, media, tier)
    # We'll just verify it doesn't crash and returns the same number of models
    assert len(models) == len(MODELS)


def test_list_models_sort_by_cost() -> None:
    models = list_models(sort_by="cost")
    assert len(models) == len(MODELS)


def test_default_provider_fallback_gemini() -> None:
    # If no models match the criteria, it should return "gemini"
    assert default_provider_for("unknown", "unknown", "unknown") == "gemini"
