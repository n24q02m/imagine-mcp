"""Guard: the installed mcp-core must ship the CF KV storage backend.

imagine-mcp's pyproject floor is >=1.18.0b2, which ALLOWS the cf-kv build
(1.18.0b5). This test fails if a relock ever resolves an older mcp-core that
lacks CfKvBackend / the cf-kv selector, which would silently break CF deploy.
"""

from importlib.metadata import version

from packaging.version import Version


def test_mcp_core_ships_cf_kv_backend():
    # The import itself is the contract: CfKvBackend + cf-kv selector exist.
    from mcp_core.storage import CfKvBackend, backend_from_env  # noqa: F401

    assert Version(version("n24q02m-mcp-core")) >= Version("1.18.0b5"), (
        "mcp-core resolved below 1.18.0b5; cf-kv backend not guaranteed. "
        "Run: uv lock --upgrade-package n24q02m-mcp-core"
    )


def test_cf_kv_selector_wired(monkeypatch):
    monkeypatch.setenv("MCP_STORAGE_BACKEND", "cf-kv")
    monkeypatch.setenv("MCP_KV_BASE_URL", "http://kv.internal")
    from mcp_core.storage import CfKvBackend, backend_from_env

    assert isinstance(backend_from_env(), CfKvBackend)
