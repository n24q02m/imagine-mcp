"""Structural guards for the relay setup config schema.

The relay form is rendered by mcp-core from this dict; a drift in field keys
or types silently breaks the browser onboarding flow, so pin the shape here.
"""

from __future__ import annotations

from imagine_mcp.relay_schema import RELAY_SCHEMA

_CREDENTIAL_KEYS = {"GEMINI_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY"}


def test_top_level_keys_present():
    for key in ("server", "displayName", "description", "fields", "capabilityInfo"):
        assert key in RELAY_SCHEMA, key
    assert RELAY_SCHEMA["server"] == "imagine-mcp"


def test_three_credential_fields_match_known_keys():
    fields = RELAY_SCHEMA["fields"]
    assert len(fields) == 3
    assert {f["key"] for f in fields} == _CREDENTIAL_KEYS


def test_all_fields_are_optional_password_inputs():
    for field in RELAY_SCHEMA["fields"]:
        assert field["type"] == "password", field["key"]
        assert field["required"] is False, field["key"]
        # Every field must give the user a way to obtain the key.
        assert field["helpUrl"].startswith("https://"), field["key"]
        assert field["helpText"], field["key"]
        assert field["label"], field["key"]


def test_capability_info_entries_well_formed():
    caps = RELAY_SCHEMA["capabilityInfo"]
    assert len(caps) == 4
    for cap in caps:
        assert cap["label"]
        assert cap["priority"]
        assert cap["description"]
