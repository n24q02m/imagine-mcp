from __future__ import annotations

import sys
from pathlib import Path

# Make scripts/ importable in tests (not a real package in the wheel)
_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.fetch_leaderboards import (  # noqa: E402
    MODEL_ALIASES,
    LBRow,
    merge_ranks,
    parse_leaderboard,
    resolve_alias,
)

from imagine_mcp.models import MODELS, UNSUPPORTED  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_aa_text_to_image() -> None:
    html = (FIXTURES / "lb_aa_text_to_image.html").read_text(encoding="utf-8")
    rows = parse_leaderboard(
        "https://artificialanalysis.ai/image/leaderboard/text-to-image", html
    )
    # Filter to our 3 providers (should exclude Black Forest Labs)
    our = [r for r in rows if r.provider in ("gemini", "openai", "grok")]
    assert len(our) == 3
    assert our[0].rank == 1
    assert our[0].provider == "gemini"
    assert our[0].model_id == "gemini-3-pro-image-preview"


def test_parse_lmarena_vision() -> None:
    html = (FIXTURES / "lb_lmarena_vision.html").read_text(encoding="utf-8")
    rows = parse_leaderboard("https://arena.ai/leaderboard/vision", html)
    assert len(rows) >= 3
    geminis = [r for r in rows if r.provider == "gemini"]
    assert geminis[0].model_id == "gemini-3.1-pro-preview"


def test_resolve_alias_known() -> None:
    assert resolve_alias("Nano Banana Pro") == "gemini-3-pro-image-preview"
    assert resolve_alias("Gemini 3 Pro") == "gemini-3.1-pro-preview"
    assert resolve_alias("gpt-5.4") == "gpt-5.4"


def test_resolve_alias_unknown_returns_none() -> None:
    assert resolve_alias("FLUX 2.0 Pro") is None


def test_merge_ranks_takes_min() -> None:
    aa = [
        LBRow(
            rank=1,
            model_id="gemini-3-pro-image-preview",
            provider="gemini",
            score=1250.0,
        )
    ]
    lm = [
        LBRow(
            rank=2,
            model_id="gemini-3-pro-image-preview",
            provider="gemini",
            score=1280.0,
        )
    ]
    merged = merge_ranks(aa, lm)
    assert merged["gemini-3-pro-image-preview"] == 1


def test_merge_ranks_missing_in_one_source() -> None:
    aa = [LBRow(rank=1, model_id="gpt-image-1.5", provider="openai", score=1220.0)]
    lm: list[LBRow] = []
    merged = merge_ranks(aa, lm)
    assert merged["gpt-image-1.5"] == 1


def test_every_canonical_id_has_alias() -> None:
    """Every non-UNSUPPORTED model_id in MODELS must map via MODEL_ALIASES."""
    canonical_ids = {e.model_id for e in MODELS if e.model_id is not UNSUPPORTED}
    alias_values = set(MODEL_ALIASES.values())
    missing = canonical_ids - alias_values
    assert not missing, f"canonical IDs missing from MODEL_ALIASES: {missing}"
