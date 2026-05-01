import pytest


@pytest.fixture(autouse=True)
def reset_clients():
    """Reset module-level _CLIENT globals before each test to ensure isolation."""
    import imagine_mcp.media
    import imagine_mcp.providers.gemini
    import imagine_mcp.providers.grok
    import imagine_mcp.providers.openai

    imagine_mcp.media._CLIENT = None
    imagine_mcp.providers.gemini._CLIENT = None
    imagine_mcp.providers.grok._CLIENT = None
    imagine_mcp.providers.openai._CLIENT = None
