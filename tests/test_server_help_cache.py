from unittest.mock import MagicMock, patch

from imagine_mcp.server import _get_help_content


def test_help_tool_caching():
    """Verify that calling the help tool multiple times only reads the file once."""

    # We want to mock the read_text call inside _get_help_content.
    # _get_help_content is already decorated with lru_cache.
    # To test it, we should clear the cache first if it was already called.
    _get_help_content.cache_clear()

    with patch("imagine_mcp.server.files") as mock_files:
        mock_file = MagicMock()
        mock_file.read_text.return_value = "mocked content"
        mock_files.return_value.joinpath.return_value = mock_file

        # In build_app, the help function is defined locally and decorated with @app.tool.
        # We can try to find it in app._tools if it exists, or just use _get_help_content
        # which is what we really want to test if it is being called.

        # Since app._tools failed, let us try to access the function by name if FastMCP allows it
        # or just test _get_help_content which is the core of the caching.

        # First call
        res1 = _get_help_content("understand")
        assert res1 == "mocked content"
        assert mock_file.read_text.call_count == 1

        # Second call (should be cached)
        res2 = _get_help_content("understand")
        assert res2 == "mocked content"
        assert mock_file.read_text.call_count == 1

        # Third call with different topic
        mock_file_config = MagicMock()
        mock_file_config.read_text.return_value = "config content"
        mock_files.return_value.joinpath.side_effect = lambda p: (
            mock_file_config if "config" in str(p) else mock_file
        )

        res3 = _get_help_content("config")
        assert res3 == "config content"
        assert mock_file_config.read_text.call_count == 1

        # Repeat config call
        res4 = _get_help_content("config")
        assert res4 == "config content"
        assert mock_file_config.read_text.call_count == 1


def test_get_help_content_directly_cached():
    """Verify _get_help_content specifically is cached."""
    _get_help_content.cache_clear()

    with patch("imagine_mcp.server.files") as mock_files:
        mock_file = MagicMock()
        mock_file.read_text.return_value = "content"
        mock_files.return_value.joinpath.return_value = mock_file

        _get_help_content("understand")
        _get_help_content("understand")

        assert mock_file.read_text.call_count == 1
