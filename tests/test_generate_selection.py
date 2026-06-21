"""GENERATE_MODELS chain + provider-priority dispatch behaviour.

Covers the generate-side model selection gap: a configured GENERATE_MODELS
chain resolves the provider from the entry prefix and OVERRIDES the catalog
``model_id`` with the entry's model segment; an unset chain keeps the catalog
default but lets GENERATE_PROVIDER_PRIORITY reorder the auto-fallback.
"""

from __future__ import annotations

import pytest

from imagine_mcp.dispatcher import dispatch_generate


@pytest.fixture
def clean_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "XAI_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "GENERATE_MODELS",
        "GENERATE_PROVIDER_PRIORITY",
    ):
        monkeypatch.delenv(var, raising=False)


@pytest.mark.asyncio
async def test_generate_chain_overrides_catalog_model_id(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GENERATE_MODELS entry's model segment replaces the catalog model_id."""
    monkeypatch.setenv("GEMINI_API_KEY", "gem-test")
    monkeypatch.setenv("GENERATE_MODELS", "gemini/my-custom-image-model")

    captured: dict[str, object] = {}

    async def mock_fn(
        prompt: str,
        tier: str,
        reference_image_url: str | None,
        aspect_ratio: str,
        output_mode: str = "both",
        model_id: str | None = None,
    ) -> dict:
        captured["provider"] = "gemini"
        captured["model_id"] = model_id
        return {"image": "...", "model": model_id, "provider": "gemini"}

    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "generate_image", mock_fn, raising=False)

    result = await dispatch_generate(
        media_type="image",
        prompt="a cat",
        provider=None,
        tier="poor",
    )
    assert captured["provider"] == "gemini"
    assert captured["model_id"] == "my-custom-image-model"
    assert result["model"] == "my-custom-image-model"


@pytest.mark.asyncio
async def test_generate_chain_resolves_provider_from_prefix(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A grok/ GENERATE_MODELS entry routes to the native grok provider."""
    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    monkeypatch.setenv("GENERATE_MODELS", "grok/grok-imagine-image-custom")

    captured: dict[str, object] = {}

    async def mock_fn(
        prompt: str,
        tier: str,
        reference_image_url: str | None,
        aspect_ratio: str,
        output_mode: str = "both",
        model_id: str | None = None,
    ) -> dict:
        captured["called"] = "grok"
        captured["model_id"] = model_id
        return {"image": "...", "model": model_id, "provider": "grok"}

    import imagine_mcp.providers.grok as grok_mod

    monkeypatch.setattr(grok_mod, "generate_image", mock_fn, raising=False)

    result = await dispatch_generate(
        media_type="image",
        prompt="a cat",
        provider=None,
        tier="poor",
    )
    assert captured["called"] == "grok"
    assert captured["model_id"] == "grok-imagine-image-custom"
    assert result["provider"] == "grok"


@pytest.mark.asyncio
async def test_generate_chain_video_override(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GENERATE_MODELS also overrides the model_id on the video path."""
    monkeypatch.setenv("GEMINI_API_KEY", "gem-test")
    monkeypatch.setenv("GENERATE_MODELS", "gemini/veo-custom")

    captured: dict[str, object] = {}

    async def mock_fn(
        prompt: str,
        tier: str,
        reference_image_url: str | None,
        job_id: str | None,
        aspect_ratio: str,
        duration_seconds: int,
        output_mode: str = "both",
        model_id: str | None = None,
    ) -> dict:
        captured["model_id"] = model_id
        return {"job_id": "j1", "status": "pending", "model": model_id}

    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "generate_video", mock_fn, raising=False)

    await dispatch_generate(
        media_type="video",
        prompt="a dog running",
        provider=None,
        tier="poor",
    )
    assert captured["model_id"] == "veo-custom"


@pytest.mark.asyncio
async def test_generate_chain_explicit_provider_ignores_chain(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicit provider keeps the catalog model_id (chain ignored)."""
    monkeypatch.setenv("GENERATE_MODELS", "gemini/should-be-ignored")

    captured: dict[str, object] = {}

    async def mock_fn(
        prompt: str,
        tier: str,
        reference_image_url: str | None,
        aspect_ratio: str,
        output_mode: str = "both",
        model_id: str | None = None,
    ) -> dict:
        captured["model_id"] = model_id
        return {"image": "...", "model": "catalog", "provider": "openai"}

    import imagine_mcp.providers.openai as openai_mod

    monkeypatch.setattr(openai_mod, "generate_image", mock_fn, raising=False)

    await dispatch_generate(
        media_type="image",
        prompt="a cat",
        provider="openai",
        tier="poor",
    )
    # Explicit provider -> catalog path -> no model_id override.
    assert captured["model_id"] is None


@pytest.mark.asyncio
async def test_generate_provider_priority_reorders_default(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With multiple keys, GENERATE_PROVIDER_PRIORITY drives the auto pick.

    Default priority is XAI > OPENAI > GEMINI; here we flip it so GEMINI wins
    even though all three keys are present.
    """
    monkeypatch.setenv("XAI_API_KEY", "x")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("GENERATE_PROVIDER_PRIORITY", "gemini,openai,grok")

    captured: dict[str, str] = {}

    async def mock_fn(
        prompt: str,
        tier: str,
        reference_image_url: str | None,
        aspect_ratio: str,
        output_mode: str = "both",
        model_id: str | None = None,
    ) -> dict:
        captured["called"] = "gemini"
        return {"image": "...", "model": "x", "provider": "gemini"}

    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "generate_image", mock_fn, raising=False)

    result = await dispatch_generate(
        media_type="image",
        prompt="a cat",
        provider=None,
        tier="poor",
    )
    assert captured["called"] == "gemini"
    assert result["provider"] == "gemini"


@pytest.mark.asyncio
async def test_generate_no_chain_keeps_catalog_default(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No GENERATE_MODELS -> catalog model_id (model_id override is None)."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    captured: dict[str, object] = {}

    async def mock_fn(
        prompt: str,
        tier: str,
        reference_image_url: str | None,
        aspect_ratio: str,
        output_mode: str = "both",
        model_id: str | None = None,
    ) -> dict:
        captured["model_id"] = model_id
        return {"image": "...", "model": "gpt-image", "provider": "openai"}

    import imagine_mcp.providers.openai as openai_mod

    monkeypatch.setattr(openai_mod, "generate_image", mock_fn, raising=False)

    await dispatch_generate(
        media_type="image",
        prompt="a cat",
        provider=None,
        tier="poor",
    )
    assert captured["model_id"] is None
