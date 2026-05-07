<<<<<<< SEARCH
from imagine_mcp.dispatcher import (
    _default_provider,
    dispatch_generate,
    dispatch_understand,
)
=======
from imagine_mcp.dispatcher import (
    GenerateRequest,
    _default_provider,
    dispatch_generate,
    dispatch_understand,
)
>>>>>>> REPLACE
<<<<<<< SEARCH
def test_generate_invalid_media_type() -> None:
    with pytest.raises(InvalidMediaTypeError):
        dispatch_generate(
            media_type="audio",
            prompt="hi",
            provider="gemini",
            tier="poor",
        )


def test_generate_unsupported_video_openai() -> None:
    with pytest.raises(ProviderUnsupportedError) as exc_info:
        dispatch_generate(
            media_type="video",
            prompt="a dog running",
            provider="openai",
            tier="poor",
        )
=======
def test_generate_invalid_media_type() -> None:
    with pytest.raises(InvalidMediaTypeError):
        dispatch_generate(
            GenerateRequest(
                media_type="audio",
                prompt="hi",
                provider="gemini",
                tier="poor",
            )
        )


def test_generate_unsupported_video_openai() -> None:
    with pytest.raises(ProviderUnsupportedError) as exc_info:
        dispatch_generate(
            GenerateRequest(
                media_type="video",
                prompt="a dog running",
                provider="openai",
                tier="poor",
            )
        )
>>>>>>> REPLACE
<<<<<<< SEARCH
def test_generate_rejects_non_http_reference_image_url() -> None:
    with pytest.raises(InvalidURLError, match="reference_image_url"):
        dispatch_generate(
            media_type="image",
            prompt="cat",
            provider="gemini",
            tier="poor",
            reference_image_url="file:///etc/passwd",
        )
=======
def test_generate_rejects_non_http_reference_image_url() -> None:
    with pytest.raises(InvalidURLError, match="reference_image_url"):
        dispatch_generate(
            GenerateRequest(
                media_type="image",
                prompt="cat",
                provider="gemini",
                tier="poor",
                reference_image_url="file:///etc/passwd",
            )
        )
>>>>>>> REPLACE
<<<<<<< SEARCH
def test_dispatch_generate_resolves_default_provider(
    clean_provider_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    captured: dict[str, str] = {}

    def mock_fn(
        prompt: str,
        tier: str,
        reference_image_url: str | None,
        aspect_ratio: str,
    ) -> dict:
        captured["called"] = "openai"
        return {"image": "...", "model": "gpt-image", "provider": "openai"}

    import imagine_mcp.providers.openai as openai_mod

    monkeypatch.setattr(openai_mod, "generate_image", mock_fn, raising=False)

    result = dispatch_generate(
        media_type="image",
        prompt="a cat",
        provider=None,
        tier="poor",
    )
    assert captured["called"] == "openai"
=======
def test_dispatch_generate_resolves_default_provider(
    clean_provider_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    captured: dict[str, str] = {}

    def mock_fn(
        prompt: str,
        tier: str,
        reference_image_url: str | None,
        aspect_ratio: str,
    ) -> dict:
        captured["called"] = "openai"
        return {"image": "...", "model": "gpt-image", "provider": "openai"}

    import imagine_mcp.providers.openai as openai_mod

    monkeypatch.setattr(openai_mod, "generate_image", mock_fn, raising=False)

    result = dispatch_generate(
        GenerateRequest(
            media_type="image",
            prompt="a cat",
            provider=None,
            tier="poor",
        )
    )
    assert captured["called"] == "openai"
>>>>>>> REPLACE
