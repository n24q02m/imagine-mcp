import pytest

import imagine_mcp.media


@pytest.fixture(autouse=True)
def reset_ssrf_safe_client():
    """Reset the global _CLIENT in imagine_mcp.media before each test."""
    if imagine_mcp.media._CLIENT is not None:
        imagine_mcp.media._CLIENT.close()
    imagine_mcp.media._CLIENT = None
    yield
    if imagine_mcp.media._CLIENT is not None:
        imagine_mcp.media._CLIENT.close()
    imagine_mcp.media._CLIENT = None
