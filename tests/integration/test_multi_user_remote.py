"""Per-sub LLM key isolation in imagine-mcp remote multi-user mode."""

from __future__ import annotations

import pytest


@pytest.mark.integration
def test_two_subs_isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("IMAGINE_DATA_DIR", str(tmp_path))
    from imagine_mcp.credential_state import read_for_sub, store_for_sub

    store_for_sub("user_a", {"GEMINI_API_KEY": "key_a"})
    store_for_sub("user_b", {"GEMINI_API_KEY": "key_b"})

    assert read_for_sub("user_a")["GEMINI_API_KEY"] == "key_a"
    assert read_for_sub("user_b")["GEMINI_API_KEY"] == "key_b"


@pytest.mark.integration
def test_save_credentials_uses_sub_when_public_url_set(tmp_path, monkeypatch):
    monkeypatch.setenv("IMAGINE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PUBLIC_URL", "https://imagine.example.com")
    from imagine_mcp.credential_state import read_for_sub, save_credentials

    save_credentials({"GEMINI_API_KEY": "k1"}, {"sub": "user_a"})
    save_credentials({"GEMINI_API_KEY": "k2"}, {"sub": "user_b"})

    assert read_for_sub("user_a")["GEMINI_API_KEY"] == "k1"
    assert read_for_sub("user_b")["GEMINI_API_KEY"] == "k2"
