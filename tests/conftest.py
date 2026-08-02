import pytest


@pytest.fixture(autouse=True)
def reset_clients():
    """Reset module-level clients before each test to ensure isolation."""
    from imagine_mcp import media
    from imagine_mcp.providers import gemini, grok, openai

    media._reset_ssrf_safe_client()

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


@pytest.fixture(autouse=True)
def _isolate_per_plugin_home(tmp_path_factory, monkeypatch):
    """Redirect ~/ to a per-test tmp dir so PerPluginStore writes don't
    pollute the real ~/.imagine-mcp/ between test runs (or worse, between
    parallel pytest workers in CI). Path.home() reads HOME on POSIX
    and USERPROFILE on Windows."""
    fake_home = tmp_path_factory.mktemp("imagine_test_home")
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
