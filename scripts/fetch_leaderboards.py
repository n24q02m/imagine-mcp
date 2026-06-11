"""Fetch Artificial Analysis + LMArena leaderboards, compute quality ranks.

Saves a raw snapshot to data/leaderboard_snapshots/<YYYY-MM-DD>.json.
Does NOT rewrite src/imagine_mcp/models.py directly -- that is the caller's job
(mise run refresh-ranks chains fetch -> gen_models_table -> tests).

See spec Section 15 for design.
"""

from __future__ import annotations

import contextlib
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup, SoupStrainer, Tag

log = logging.getLogger("refresh_ranks")

def _sanitize_text(text: str) -> str:
    """Sanitize parsed text to prevent terminal injection and ReDoS."""
    # Strip control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # Truncate to a reasonable maximum length
    if len(text) > 500:
        return text[:500] + "..."
    return text


LB_URLS: list[str] = [
    "https://artificialanalysis.ai/image/leaderboard/text-to-image",
    "https://artificialanalysis.ai/image/leaderboard/editing",
    "https://artificialanalysis.ai/video/leaderboard/text-to-video",
    "https://artificialanalysis.ai/video/leaderboard/image-to-video",
    "https://arena.ai/leaderboard/vision",
    "https://arena.ai/leaderboard/text-to-image",
    "https://arena.ai/leaderboard/image-edit",
    "https://arena.ai/leaderboard/text-to-video",
    "https://arena.ai/leaderboard/image-to-video",
    "https://arena.ai/leaderboard/video-edit",
]

_PROVIDER_NORMALIZE: dict[str, str] = {
    "google": "gemini",
    "google deepmind": "gemini",
    "deepmind": "gemini",
    "openai": "openai",
    "xai": "grok",
    "x.ai": "grok",
    "x ai": "grok",
}

# Display-name -> canonical model_id. Update when new model appears in LB.
MODEL_ALIASES: dict[str, str] = {
    # Gemini understand (vision)
    "Gemini 3 Pro": "gemini-3.1-pro-preview",
    "gemini-3.1-pro-preview": "gemini-3.1-pro-preview",
    "Gemini 3 Flash Lite": "gemini-3.1-flash-lite-preview",
    "gemini-3.1-flash-lite-preview": "gemini-3.1-flash-lite-preview",
    # Gemini generate image
    "Nano Banana Pro": "gemini-3-pro-image-preview",
    "gemini-3-pro-image-preview": "gemini-3-pro-image-preview",
    "Nano Banana 2": "gemini-3.1-flash-image-preview",
    "gemini-3.1-flash-image-preview": "gemini-3.1-flash-image-preview",
    # Gemini generate video
    "Veo 3.1 Lite": "veo-3.1-lite-generate-preview",
    "veo-3.1-lite-generate-preview": "veo-3.1-lite-generate-preview",
    "Veo 3.1": "veo-3.1-generate-preview",
    "veo-3.1-generate-preview": "veo-3.1-generate-preview",
    # OpenAI understand
    "GPT-5.4": "gpt-5.4",
    "gpt-5.4": "gpt-5.4",
    "GPT-5.4 Mini": "gpt-5.4-mini",
    "gpt-5.4-mini": "gpt-5.4-mini",
    # OpenAI generate image
    "gpt-image-1.5": "gpt-image-1.5",
    "gpt-image-1-mini": "gpt-image-1-mini",
    # Grok understand
    "Grok 4.20 Reasoning": "grok-4.20-0309-reasoning",
    "grok-4.20-0309-reasoning": "grok-4.20-0309-reasoning",
    "Grok 4.20": "grok-4.20-0309-non-reasoning",
    "grok-4.20-0309-non-reasoning": "grok-4.20-0309-non-reasoning",
    # Grok generate
    "Aurora": "grok-imagine-image",
    "grok-imagine-image": "grok-imagine-image",
    "Grok Imagine Pro": "grok-imagine-image-pro",
    "grok-imagine-image-pro": "grok-imagine-image-pro",
    "Grok Imagine Video": "grok-imagine-video",
    "grok-imagine-video": "grok-imagine-video",
}


@dataclass(frozen=True)
class LBRow:
    rank: int
    model_id: str
    provider: str
    score: float | None = None
    cost_per_call_usd: float | None = None


def resolve_alias(display_name: str) -> str | None:
    """Return canonical model_id for a leaderboard display name, or None if unknown."""
    key = display_name.strip()
    return MODEL_ALIASES.get(key)


def _normalize_provider(raw: str) -> str | None:
    key = raw.lower().strip().split("·")[0].strip()  # split on "middle dot"
    return _PROVIDER_NORMALIZE.get(key)


def _infer_provider_from_id(model_id: str) -> str | None:
    lid = model_id.lower()
    if lid.startswith(("gemini", "veo", "imagen")):
        return "gemini"
    if lid.startswith(("gpt", "dall", "sora")):
        return "openai"
    if lid.startswith(("grok", "aurora")):
        return "grok"
    return None


def _parse_row(
    cells: list[Tag], rank_i: int, name_i: int, provider_i: int, score_i: int, url: str
) -> LBRow | None:
    """Parse a single row from the leaderboard table."""
    if len(cells) <= rank_i:
        return None

    rank_text = _sanitize_text(cells[rank_i].get_text())
    rank_match = re.search(r"\d+", rank_text)
    if not rank_match:
        return None
    rank = int(rank_match.group())

    name_cell = cells[name_i]
    link = name_cell.find("a")
    raw_display = link.get_text(strip=True) if link else name_cell.get_text(strip=True)
    display = _sanitize_text(raw_display)
    # Strip trailing "provider . type" annotations LMArena embeds
    display = re.split(r"\s*·\s*|\s+xAI\s+|\s+OpenAI\s+|\s+Google\s+", display)[
        0
    ].strip()

    model_id = resolve_alias(display)
    if not model_id:
        log.info("unknown alias (skip): %r in %s", display, url)
        return None

    provider: str | None = None
    if provider_i >= 0:
        provider_raw = _sanitize_text(cells[provider_i].get_text(strip=True))
        if provider_raw:
            provider = _normalize_provider(provider_raw)
    if not provider:
        provider = _infer_provider_from_id(model_id)
    if not provider:
        return None

    score: float | None = None
    if score_i >= 0:
        score_text = _sanitize_text(cells[score_i].get_text())
        score_match = re.search(r"[\d.]+", score_text)
        if score_match:
            with contextlib.suppress(ValueError):
                score = float(score_match.group())

    return LBRow(rank=rank, model_id=model_id, provider=provider, score=score)


def parse_leaderboard(url: str, html: str) -> list[LBRow]:
    """Extract ranked rows filtered to {gemini, openai, grok}."""
    old_limit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(2000)
        strainer = SoupStrainer("table")
        soup = BeautifulSoup(html, "html.parser", parse_only=strainer)
        table = soup.find("table")
        if not table:
            log.warning("no table found: %s", url)
            return []

        thead = table.find("thead")
        if not thead:
            log.warning("no thead: %s", url)
            return []
        header_cells = [_sanitize_text(c.get_text(strip=True)).lower() for c in thead.find_all("th")]

        try:
            rank_i = header_cells.index("rank")
        except ValueError:
            log.warning("no rank column: %s", url)
            return []

        name_i = next((i for i, c in enumerate(header_cells) if c in ("model", "name")), 1)
        provider_i = next((i for i, c in enumerate(header_cells) if "provider" in c), -1)
        score_i = next(
            (i for i, c in enumerate(header_cells) if c in ("score", "elo", "arena score")),
            -1,
        )

        tbody = table.find("tbody")
        if not tbody:
            return []

        rows: list[LBRow] = []
        for tr in tbody.find_all("tr"):
            row = _parse_row(
                tr.find_all("td"),
                rank_i=rank_i,
                name_i=name_i,
                provider_i=provider_i,
                score_i=score_i,
                url=url,
            )
            if row:
                rows.append(row)

    finally:
        sys.setrecursionlimit(old_limit)

    return rows


def merge_ranks(rows_aa: list[LBRow], rows_lmarena: list[LBRow]) -> dict[str, int]:
    """Return {canonical_model_id: quality_rank} using min(rank_aa, rank_lmarena)."""
    # ⚡ Bolt: O(N) dictionary-based accumulator to efficiently process combined rank lists,
    # eliminating slower O(N^2) nested list searches.
    result: dict[str, int] = {}
    for rows in (rows_aa, rows_lmarena):
        for row in rows:
            if row.model_id in result:
                result[row.model_id] = min(result[row.model_id], row.rank)
            else:
                result[row.model_id] = row.rank
    return result


def fetch_all(client: httpx.Client) -> dict[str, list[LBRow]]:
    out: dict[str, list[LBRow]] = {}
    max_size = 5 * 1024 * 1024  # 5MB limit
    for url in LB_URLS:
        try:
            html_chunks = []
            bytes_read = 0
            with client.stream("GET", url, timeout=30.0, follow_redirects=True) as r:
                r.raise_for_status()
                for chunk in r.iter_text():
                    bytes_read += len(chunk.encode("utf-8"))
                    if bytes_read > max_size:
                        raise ValueError(f"Response exceeded 5MB limit: {url}")
                    html_chunks.append(chunk)

            html = "".join(html_chunks)
            out[url] = parse_leaderboard(url, html)
            log.info("fetched %s: %d rows after filter", url, len(out[url]))
        except Exception as exc:
            log.error("fetch failed %s: %s", url, exc)
            out[url] = []
    return out


def save_snapshot(data: dict[str, list[LBRow]], snap_dir: Path) -> Path:
    snap_dir.mkdir(parents=True, exist_ok=True)
    snapshot: dict[str, Any] = {
        "fetched_at_utc": datetime.now(UTC).isoformat(),
        "urls": {url: [asdict(r) for r in rows] for url, rows in data.items()},
    }
    today = date.today().isoformat()
    path = snap_dir / f"{today}.json"
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    repo_root = Path(__file__).resolve().parent.parent
    snap_dir = repo_root / "data" / "leaderboard_snapshots"

    with httpx.Client(
        headers={"user-agent": "imagine-mcp refresh-ranks/1.0"}
    ) as client:
        data = fetch_all(client)

    path = save_snapshot(data, snap_dir)
    log.info("snapshot saved: %s", path.name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
