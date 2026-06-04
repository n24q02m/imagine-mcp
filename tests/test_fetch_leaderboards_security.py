from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import httpx

# Make scripts/ importable
_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.fetch_leaderboards import fetch_all, parse_leaderboard  # noqa: E402


def test_fetch_all_limit_size():
    """Ensure fetch_all handles or skips oversized responses."""
    url = "https://arena.ai/leaderboard/vision"
    # 6MB of junk
    oversized_content = ("A" * (6 * 1024 * 1024)).encode("utf-8")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Length": str(len(oversized_content))}
    mock_response.iter_bytes.return_value = [oversized_content]
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock(spec=httpx.Client)
    # mock_client.stream returns a context manager
    mock_client.stream.return_value.__enter__.return_value = mock_response

    results = fetch_all(mock_client)
    assert results.get(url) == []


def test_fetch_all_limit_size_streaming():
    """Ensure fetch_all handles or skips oversized responses during streaming."""
    url = "https://arena.ai/leaderboard/vision"
    # Stream chunks that eventually exceed 5MB
    chunks = [b"A" * (1024 * 1024)] * 6

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}  # No content-length
    mock_response.iter_bytes.return_value = chunks
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.stream.return_value.__enter__.return_value = mock_response

    results = fetch_all(mock_client)
    assert results.get(url) == []


def test_parse_leaderboard_malformed_html():
    """Ensure parser doesn't crash on malicious nesting."""
    url = "https://example.com/lb"
    # Deeply nested tags to trigger recursion limit or slow parsing
    malicious_html = (
        "<div>" * 1000
        + "<table><thead><tr><th>Rank</th><th>Model</th></tr></thead><tbody><tr><td>1</td><td>Gemini 3 Pro</td></tr></tbody></table>"
        + "</div>" * 1000
    )
    rows = parse_leaderboard(url, malicious_html)
    assert len(rows) == 1
    assert rows[0].rank == 1


def test_parse_leaderboard_payload_in_text():
    """Ensure data extracted doesn't contain malicious-looking payloads."""
    url = "https://example.com/lb"
    malicious_html = """
    <table>
        <thead><tr><th>Rank</th><th>Model</th></tr></thead>
        <tbody>
            <tr>
                <td>1 <script>alert(1)</script></td>
                <td>Gemini 3 Pro <img src=x onerror=alert(1)></td>
            </tr>
        </tbody>
    </table>
    """
    rows = parse_leaderboard(url, malicious_html)
    assert len(rows) == 1
    assert rows[0].rank == 1
    # Check that model_id is a valid canonical ID from MODEL_ALIASES, not the raw malicious string
    assert rows[0].model_id == "gemini-3.1-pro-preview"


def test_parse_leaderboard_no_table_outside_strainer():
    """Ensure we only parse the table if we use SoupStrainer."""
    url = "https://example.com/lb"
    html = "<html><body><div id='malicious'>Some malicious content</div><table><thead><tr><th>Rank</th><th>Model</th></tr></thead><tbody><tr><td>1</td><td>Gemini 3 Pro</td></tr></tbody></table></body></html>"
    rows = parse_leaderboard(url, html)
    assert len(rows) == 1
