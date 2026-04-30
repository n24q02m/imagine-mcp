import pytest


@pytest.fixture(autouse=True)
def reset_media_client():
    """Reset the module-level SSRF safe client to ensure test isolation."""
    import imagine_mcp.media

    imagine_mcp.media._CLIENT = None
