import pytest


@pytest.fixture(autouse=True)
def reset_clients():
    """Reset module-level clients before each test to ensure isolation."""
    from imagine_mcp import media
    from imagine_mcp.providers import gemini, grok, openai

    media._CLIENT = None

    if hasattr(grok, "_CLIENT"):
        grok._CLIENT = None

    if hasattr(gemini, "_CLIENT"):
        gemini._CLIENT = None

    if hasattr(openai, "_CLIENT"):
        openai._CLIENT = None
