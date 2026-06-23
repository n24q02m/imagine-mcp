from __future__ import annotations

from imagine_mcp.media import _extract_extension


def test_extract_extension_security() -> None:
    # Valid extensions
    assert _extract_extension("https://example.com/foo.png") == ".png"
    assert _extract_extension("https://example.com/foo.jpg") == ".jpg"
    assert _extract_extension("https://example.com/foo.jpeg") == ".jpeg"
    assert _extract_extension("https://example.com/foo.MP4") == ".mp4"

    # Valid extensions with query/fragment
    assert _extract_extension("https://example.com/foo.png?q=1") == ".png"
    assert _extract_extension("https://example.com/foo.png#hash") == ".png"

    # Overly long extensions (> 10 chars after dot)
    assert _extract_extension("https://example.com/foo.verylongextension") == ""
    assert _extract_extension("https://example.com/foo.abcdefghijk") == ""  # 11 chars
    assert (
        _extract_extension("https://example.com/foo.abcdefghij") == ".abcdefghij"
    )  # 10 chars

    # Non-alphanumeric extensions
    assert (
        _extract_extension("https://example.com/foo.png.php") == ".php"
    )  # This is fine, it gets the last one
    assert _extract_extension("https://example.com/foo.p_n") == ""
    assert _extract_extension("https://example.com/foo.p-n") == ""

    # No extension or empty extension
    assert _extract_extension("https://example.com/foo") == ""
    assert _extract_extension("https://example.com/foo.") == ""

    # Edge cases
    assert _extract_extension("https://example.com/.ssh/config") == ""
    assert (
        _extract_extension("https://example.com/foo.123") == ".123"
    )  # Alphanumeric includes numbers
