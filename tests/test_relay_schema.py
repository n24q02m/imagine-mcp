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


def test_model_chain_tasks_are_understand_and_generate():
    tasks = {
        f["task"] for f in RELAY_SCHEMA["fields"] if f.get("type") == "model-chain"
    }
    assert tasks == {"understand", "generate"}


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


def test_understand_catalog_driven_generate_keeps_grok_supplement():
    # understand is fully catalog-driven (litellm chat catalog covers it); generate
    # keeps ONLY the grok models litellm cannot list (no gemini/openai hardcode).
    by_key = {f["key"]: f for f in RELAY_SCHEMA["fields"]}
    assert not by_key["UNDERSTAND_MODELS"].get("suggestedModels")
    gen = by_key["GENERATE_MODELS"].get("suggestedModels", [])
    assert gen, "generate must keep a minimal grok supplement litellm lacks"
    assert all("grok" in m for m in gen), f"only grok supplement expected, got {gen}"
    assert not any(m.startswith(("gemini/", "openai/")) for m in gen)
