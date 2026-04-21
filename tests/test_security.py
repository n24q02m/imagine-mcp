from __future__ import annotations
import pytest
from imagine_mcp.server import dispatch

def test_dispatch_rejects_non_http_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    # Need to verify that the understand path in gemini rejects local files
    with pytest.raises(ValueError, match="Invalid image_url scheme"):
        dispatch(
            action="understand",
            provider="gemini",
            tier="poor",
            image_url="file:///etc/passwd",
            prompt="describe",
        )
