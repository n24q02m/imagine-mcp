import pytest


@pytest.fixture(autouse=True)
def reset_clients():
    """Reset module-level clients before each test to ensure isolation."""
    from imagine_mcp import media
    from imagine_mcp.providers import gemini, grok, openai

    if hasattr(media, "_reset_ssrf_safe_client"):
        media._reset_ssrf_safe_client()
    else:
        media._CLIENT = None

    if hasattr(grok, "_CLIENT"):
        grok._CLIENT = None

    if hasattr(gemini, "_CLIENT"):
        gemini._CLIENT = None

    if hasattr(openai, "_CLIENT"):
        openai._CLIENT = None


@pytest.fixture(autouse=True)
def reset_contextvars():
    from imagine_mcp.credential_state import _request_creds

    _request_creds.set(None)
