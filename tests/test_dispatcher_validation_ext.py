from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from imagine_mcp.dispatcher import (
    _passthrough_api_key,
    dispatch_generate,
    dispatch_understand,
    resolve_generate_provider_priority,
)
from imagine_mcp.errors import (
    CredentialMissingError,
    InvalidMediaTypeError,
    InvalidURLError,
)


@pytest.fixture
def clean_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no provider API key is leaking from the host environment."""
    for var in ("XAI_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(var, raising=False)


@pytest.mark.asyncio
async def test_dispatch_understand_empty_media_urls() -> None:
    with pytest.raises(InvalidMediaTypeError, match="media_urls is empty"):
        await dispatch_understand(
            media_urls=[],
            prompt="describe",
            provider="gemini",
            tier="poor",
        )


@pytest.mark.asyncio
async def test_dispatch_understand_validate_url_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mock_validate(url: str, param: str) -> None:
        raise InvalidURLError("mocked failure")

    monkeypatch.setattr("imagine_mcp.dispatcher.validate_url_and_get_ip", mock_validate)

    with pytest.raises(InvalidURLError, match="mocked failure"):
        await dispatch_understand(
            media_urls=["https://example.com/cat.png"],
            prompt="describe",
            provider="gemini",
            tier="poor",
        )


@pytest.mark.asyncio
async def test_passthrough_understand_empty_media_urls() -> None:
    # Trigger passthrough by providing a model
    with pytest.raises(InvalidMediaTypeError, match="media_urls is empty"):
        await dispatch_understand(
            media_urls=[],
            prompt="describe",
            provider=None,
            tier="poor",
            model="openai/gpt-4o",
        )


@pytest.mark.asyncio
async def test_dispatch_understand_detect_media_type_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type_async",
        AsyncMock(side_effect=Exception("detect failure")),
    )
    # Stub URL validation so it doesn't fail first
    monkeypatch.setattr(
        "imagine_mcp.dispatcher._validate_url", AsyncMock(return_value=None)
    )

    with pytest.raises(Exception, match="detect failure"):
        await dispatch_understand(
            media_urls=["https://example.com/cat.png"],
            prompt="describe",
            provider="gemini",
            tier="poor",
        )


@pytest.mark.asyncio
async def test_dispatch_understand_gemini_multimodal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_multimodal = AsyncMock(return_value={"text": "multimodal ok"})
    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "understand_multimodal", mock_multimodal)
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type_async",
        AsyncMock(return_value="image"),
    )
    monkeypatch.setattr(
        "imagine_mcp.dispatcher._validate_url", AsyncMock(return_value=None)
    )

    result = await dispatch_understand(
        media_urls=["https://example.com/1.png", "https://example.com/2.png"],
        prompt="describe",
        provider="gemini",
        tier="poor",
    )
    assert result == {"text": "multimodal ok"}
    assert mock_multimodal.called


@pytest.mark.asyncio
async def test_dispatch_understand_video(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_video = AsyncMock(return_value={"text": "video ok"})
    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "understand_video", mock_video)
    monkeypatch.setattr(
        "imagine_mcp.dispatcher.detect_media_type_async",
        AsyncMock(return_value="video"),
    )
    monkeypatch.setattr(
        "imagine_mcp.dispatcher._validate_url", AsyncMock(return_value=None)
    )

    result = await dispatch_understand(
        media_urls=["https://example.com/video.mp4"],
        prompt="describe",
        provider="gemini",
        tier="poor",
    )
    assert result == {"text": "video ok"}
    assert mock_video.called


@pytest.mark.asyncio
async def test_dispatch_generate_video(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_gen_video = AsyncMock(return_value={"video": "ok"})
    import imagine_mcp.providers.gemini as gemini_mod

    monkeypatch.setattr(gemini_mod, "generate_video", mock_gen_video)
    monkeypatch.setattr(
        "imagine_mcp.dispatcher._validate_url", AsyncMock(return_value=None)
    )

    result = await dispatch_generate(
        media_type="video",
        prompt="a video",
        provider="gemini",
        tier="poor",
    )
    assert result == {"video": "ok"}
    assert mock_gen_video.called


@pytest.mark.asyncio
async def test_default_provider_credential_missing(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Ensure no credentials are set in PerPluginStore either
    monkeypatch.setattr(
        "imagine_mcp.credential_state.credentials_for_current_request",
        lambda: {},
    )

    with pytest.raises(CredentialMissingError, match="No provider API key configured"):
        await dispatch_understand(
            media_urls=["https://example.com/cat.png"],
            prompt="describe",
            provider=None,
            tier="poor",
        )


@pytest.mark.asyncio
async def test_dispatch_generate_validate_url_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mock_validate(url: str, param: str) -> None:
        raise InvalidURLError("mocked failure")

    monkeypatch.setattr("imagine_mcp.dispatcher.validate_url_and_get_ip", mock_validate)

    with pytest.raises(InvalidURLError, match="mocked failure"):
        await dispatch_generate(
            media_type="image",
            prompt="a cat",
            provider="gemini",
            tier="poor",
            reference_image_url="https://example.com/ref.png",
        )


def test_resolve_generate_provider_priority_custom(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "imagine_mcp.credential_state.config_value_for_current_request",
        lambda x: "openai,gemini" if x == "GENERATE_PROVIDER_PRIORITY" else None,
    )
    assert resolve_generate_provider_priority() == ["openai", "gemini"]


@pytest.mark.asyncio
async def test_passthrough_understand_validate_url_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mock_validate(url: str, param: str) -> None:
        raise InvalidURLError("mocked failure")

    monkeypatch.setattr("imagine_mcp.dispatcher.validate_url_and_get_ip", mock_validate)
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    with pytest.raises(InvalidURLError, match="mocked failure"):
        await dispatch_understand(
            media_urls=["https://example.com/cat.png"],
            prompt="describe",
            provider=None,
            tier="poor",
            model="openai/gpt-4o",
        )


@pytest.mark.asyncio
async def test_dispatch_generate_resolve_chain_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GENERATE_MODELS", "openai/dall-e-3")
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    mock_gen_image = AsyncMock(return_value={"image": "ok"})
    import imagine_mcp.providers.openai as openai_mod

    monkeypatch.setattr(openai_mod, "generate_image", mock_gen_image)

    result = await dispatch_generate(
        media_type="image",
        prompt="a cat",
        provider=None,
        tier="poor",
    )
    assert result == {"image": "ok"}
    assert mock_gen_image.called


def test_passthrough_api_key_none() -> None:
    assert _passthrough_api_key("unknown/model") is None


@pytest.mark.asyncio
async def test_passthrough_understand_gather_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Coverage for line 272
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(
        "imagine_mcp.dispatcher._validate_url",
        AsyncMock(side_effect=Exception("gather error")),
    )

    with pytest.raises(Exception, match="gather error"):
        await dispatch_understand(
            media_urls=["https://example.com/cat.png"],
            prompt="describe",
            provider=None,
            tier="poor",
            model="openai/gpt-4o",
        )


@pytest.mark.asyncio
async def test_default_generate_provider_credential_missing(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Coverage for line 139-140 via dispatch_generate
    monkeypatch.setattr(
        "imagine_mcp.credential_state.credentials_for_current_request",
        lambda: {},
    )

    with pytest.raises(CredentialMissingError, match="No provider API key configured"):
        await dispatch_generate(
            media_type="image",
            prompt="a cat",
            provider=None,
            tier="poor",
        )


@pytest.mark.asyncio
async def test_passthrough_understand_download_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Coverage for line 272
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    # Bypass validation
    monkeypatch.setattr(
        "imagine_mcp.dispatcher._validate_url", AsyncMock(return_value=None)
    )
    # Mock capability check and completion
    from mcp_core import llm

    monkeypatch.setattr(llm, "check_capability", lambda *a, **k: None)

    # Mock SSRF client to fail
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("download fail")
    import imagine_mcp.media as media_mod

    monkeypatch.setattr(media_mod, "get_ssrf_safe_async_client", lambda: mock_client)

    with pytest.raises(Exception, match="download fail"):
        await dispatch_understand(
            media_urls=["https://example.com/cat.png"],
            prompt="describe",
            provider=None,
            tier="poor",
            model="openai/gpt-4o",
        )
