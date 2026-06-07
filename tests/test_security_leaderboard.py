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


def test_parse_leaderboard_sanitizes_control_characters():
    # Payload with ANSI escape sequences and other control characters.
    # After fix, we want it to resolve "Gemini 3 Pro" by sanitizing the input.
    html = """
    <table>
        <thead><tr><th>Rank</th><th>Model</th></tr></thead>
        <tbody>
            <tr>
                <td>1</td>
                <td>Gemini 3 Pro\x1b[2J\x00\x01\x02</td>
            </tr>
        </tbody>
    </table>
    """
    rows = parse_leaderboard("http://example.com", html)
    assert len(rows) == 1
    assert rows[0].model_id == "gemini-3.1-pro-preview"


def test_parse_leaderboard_huge_string_no_redos():
    # Attempt to trigger ReDoS with a long string that partially matches but fails at the end.
    # The regex is r"\s*·\s*|\s+xAI\s+|\s+OpenAI\s+|\s+Google\s+"
    huge_name = "Gemini 3 Pro" + (" " * 100000) + "xAI"
    html = f"""
    <table>
        <thead><tr><th>Rank</th><th>Name</th></tr></thead>
        <tbody>
            <tr><td>1</td><td>{huge_name}</td></tr>
        </tbody>
    </table>
    """
    # This should be fast now because it's truncated before regex
    rows = parse_leaderboard("http://example.com", html)
    assert len(rows) == 1
    assert rows[0].model_id == "gemini-3.1-pro-preview"


def test_parse_leaderboard_deep_nesting_is_safe():
    # Test for potential RecursionError.
    # BS4 with html.parser is generally good, but 10000 might hit limits.
    levels = 5000
    nested_html = (
        "<div>" * levels
        + "<table><thead><tr><th>Rank</th><th>Model</th></tr></thead></table>"
        + "</div>" * levels
    )
    # Should not crash
    rows = parse_leaderboard("http://example.com", nested_html)
    assert rows == []


def test_fetch_all_enforces_size_limit():
    mock_client = MagicMock(spec=httpx.Client)

    # We need to mock the context manager for client.stream
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Length": str(10 * 1024 * 1024)}  # 10MB

    mock_client.stream.return_value.__enter__.return_value = mock_response

    results = fetch_all(mock_client)
    # It should have caught the error and returned empty list for that URL
    assert (
        results["https://artificialanalysis.ai/image/leaderboard/text-to-image"] == []
    )


def test_fetch_all_enforces_chunk_size_limit():
    mock_client = MagicMock(spec=httpx.Client)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}  # No content length
    # Mock iter_text to return large chunks
    mock_response.iter_text.return_value = ["A" * 1024 * 1024] * 6  # 6MB total

    mock_client.stream.return_value.__enter__.return_value = mock_response

    results = fetch_all(mock_client)
    assert (
        results["https://artificialanalysis.ai/image/leaderboard/text-to-image"] == []
    )


def test_parse_leaderboard_no_thead_robustness():
    html = "<table><tbody><tr><td>1</td><td>Gemini 3 Pro</td></tr></tbody></table>"
    rows = parse_leaderboard("http://example.com", html)
    assert rows == []  # Current logic requires thead
