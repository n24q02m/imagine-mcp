"""Guard: the autouse home-isolation fixture in conftest must stay in place.

``PerPluginStore`` keys its on-disk layout off ``Path.home()``
(``~/.imagine-mcp/config.json`` plus the machine key at
``~/.imagine-mcp/.secret``), so an un-isolated run writes into the
developer's real home -- and into one shared home when CI runs parallel
pytest workers. If ``_isolate_per_plugin_home`` is deleted or stops
working, these tests fail loudly instead of letting the suite silently
read and overwrite real credentials.

Both assertions are non-destructive: they inspect resolved paths rather
than performing a store write, so a regression reports the problem
without itself polluting the real home.
"""

from pathlib import Path

from imagine_mcp.credential_state import PLUGIN_NAME

# Captured at import (collection) time, before any autouse fixture has
# redirected HOME/USERPROFILE -- so this is the real user home.
_REAL_HOME = Path.home()
_REAL_STORE = _REAL_HOME / f".{PLUGIN_NAME}-mcp"


def test_home_is_redirected_away_from_real_home():
    """Path.home() inside a test must not resolve to the real user home."""
    assert Path.home() != _REAL_HOME, (
        "home-isolation fixture is missing: Path.home() still resolves to the "
        f"real user home ({_REAL_HOME}). Restore _isolate_per_plugin_home in "
        "tests/conftest.py."
    )


def test_per_plugin_store_path_is_outside_real_home():
    """The credential store must not resolve into the real ~/.imagine-mcp."""
    from mcp_core.storage.per_plugin_store import PerPluginStore

    cred_path = PerPluginStore(PLUGIN_NAME).cred_path

    assert _REAL_STORE not in cred_path.parents, (
        f"PerPluginStore would read/write the real credential store: {cred_path}. "
        "Restore _isolate_per_plugin_home in tests/conftest.py."
    )
