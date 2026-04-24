from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.gen_models_table import render_markdown  # noqa: E402

from imagine_mcp.models import MODELS, UNSUPPORTED  # noqa: E402


def test_render_contains_all_live_entries() -> None:
    md = render_markdown(MODELS)
    live = [e for e in MODELS if e.model_id is not UNSUPPORTED]
    for e in live:
        assert str(e.model_id) in md, f"missing {e.model_id}"


def test_render_is_stable() -> None:
    md1 = render_markdown(MODELS)
    md2 = render_markdown(MODELS)
    assert md1 == md2, "render_markdown must be deterministic"


def test_render_sorted_by_rank_within_group() -> None:
    md = render_markdown(MODELS)
    # generate/image/rich section: rank 1 gemini must appear before rank 2 openai
    section = md.split("## generate / image / rich")[1].split("## ")[0]
    gemini_pos = section.find("gemini")
    openai_pos = section.find("openai")
    assert gemini_pos >= 0 and openai_pos >= 0
    assert gemini_pos < openai_pos


def test_render_marks_unsupported_as_error() -> None:
    md = render_markdown(MODELS)
    # openai video understand should be ERROR
    assert "**ERROR**" in md


def test_drift_check_against_committed_docs_models() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    committed = repo_root / "docs" / "models.md"
    if not committed.exists():
        return  # first run, docs/models.md not yet generated
    regen = render_markdown(MODELS)
    assert committed.read_text(encoding="utf-8") == regen, (
        "docs/models.md drift detected. "
        "Run `python scripts/gen_models_table.py` and commit."
    )
