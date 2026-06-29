from __future__ import annotations

import pytest

from imagine_mcp import models
from imagine_mcp.models import _BASELINE_DATE, ModelEntry, default_provider_for


def test_default_provider_fallback_no_candidates() -> None:
    """Test fallback when no candidates are found for a combo."""
    default_provider_for.cache_clear()
    # unknown combo results in empty candidates
    assert default_provider_for("missing_action", "image", "poor") == "gemini"


def test_default_provider_fallback_unranked_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test fallback when candidates exist but the top one has no rank."""
    default_provider_for.cache_clear()

    # Create a mock entry that is supported but has no rank
    unranked_entry = ModelEntry(
        provider="openai",
        action="test_action",
        media="image",
        tier="poor",
        model_id="gpt-test",
        quality_rank=None,
        cost_tier="low",
        last_verified=_BASELINE_DATE,
    )

    # Patch MODELS so list_models finds our unranked entry
    monkeypatch.setattr(models, "MODELS", [unranked_entry])

    # Should fall back to gemini because quality_rank is None
    assert default_provider_for("test_action", "image", "poor") == "gemini"
