from unittest.mock import MagicMock, patch

import pytest

from imagine_mcp.server import _get_help_content, build_app


@pytest.mark.asyncio
async def test_help_caching():
    # Clear cache if it exists (for repeated test runs in same process, though unlikely here)
    _get_help_content.cache_clear()

    try:
        with patch("imagine_mcp.server.files") as mock_files:
            mock_path = MagicMock()
            mock_path.joinpath.return_value.read_text.return_value = "cached content"
            mock_files.return_value = mock_path

            app = build_app()

            # Call help twice
            # FastMCP tools can be called directly if we find them
            help_tool = None
            for tool in await app.list_tools():
                if tool.name == "help":
                    help_tool = tool.fn
                    break

            assert help_tool is not None

            res1 = await help_tool("understand")
            res2 = await help_tool("understand")

            assert res1 == "cached content"
            assert res2 == "cached content"

            # Verify read_text was called only once due to caching
            assert mock_path.joinpath.return_value.read_text.call_count == 1
    finally:
        # Clear the mocked "cached content" so the module-level @cache does not
        # leak into other tests (e.g. test_server.py::test_tool_help).
        _get_help_content.cache_clear()
