from __future__ import annotations

from imagine_mcp.media import _extract_extension


def test_extract_extension_valid() -> None:
    assert _extract_extension("https://example.com/foo.png") == ".png"
    assert _extract_extension("https://example.com/foo.jpg") == ".jpg"
    assert _extract_extension("https://example.com/foo.mp4") == ".mp4"
    assert _extract_extension("https://example.com/foo.PNG") == ".png"
    assert _extract_extension("https://example.com/foo.mp4?q=1") == ".mp4"
    assert _extract_extension("https://example.com/foo.mp4#hash") == ".mp4"


def test_extract_extension_invalid_length() -> None:
    assert _extract_extension("https://example.com/foo.") == ""
    assert _extract_extension("https://example.com/foo.a") == ".a"
    assert _extract_extension("https://example.com/foo.abcdefghij") == ".abcdefghij"
    assert _extract_extension("https://example.com/foo.abcdefghijk") == ""


def test_extract_extension_invalid_characters() -> None:
    assert _extract_extension("https://example.com/foo.png\x00") == ""
    assert _extract_extension("https://example.com/foo.p-g") == ""
    assert _extract_extension("https://example.com/foo.p_g") == ""
    assert _extract_extension("https://example.com/foo.png%20") == ""


def test_extract_extension_no_extension() -> None:
    assert _extract_extension("https://example.com/foo") == ""
    assert _extract_extension("https://example.com/foo/") == ""
    assert _extract_extension("https://example.com/foo?q=1") == ""
    assert _extract_extension("https://example.com/foo#hash") == ""


def test_extract_extension_double_extension() -> None:
    assert _extract_extension("https://example.com/foo.tar.gz") == ".gz"
