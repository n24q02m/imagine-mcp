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


def test_exactly_one_model_chain_task_understand():
    tasks = {
        f["task"] for f in RELAY_SCHEMA["fields"] if f.get("type") == "model-chain"
    }
    assert tasks == {"understand"}


def test_derived_keys_are_the_three_providers():
    derived = {f["key"] for f in RELAY_SCHEMA["fields"] if f.get("derived")}
    assert derived == _CREDENTIAL_KEYS


def test_no_priority_arrow_strings():
    for cap in RELAY_SCHEMA["capabilityInfo"]:
        assert ">" not in cap.get("priority", ""), cap


def test_every_suggested_model_has_a_provider_prefix():
    for field in RELAY_SCHEMA["fields"]:
        for model in field.get("suggestedModels", []):
            assert "/" in model, model


def test_capability_info_entries_well_formed():
    caps = RELAY_SCHEMA["capabilityInfo"]
    assert caps
    for cap in caps:
        assert cap["label"]
        assert cap["priority"]
        assert cap["description"]
