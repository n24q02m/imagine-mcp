<<<<<<< SEARCH
def dispatch_generate(
    media_type: str,
    prompt: str,
    provider: str | None,
    tier: str,
    reference_image_url: str | None = None,
    job_id: str | None = None,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
) -> dict[str, Any]:
    """Dispatch generate call to provider.

    When ``provider`` is ``None``, auto-resolve via :func:`_default_provider`
    (first provider whose API key is present in the environment).
    """
    if provider is None:
        provider = _default_provider()
    _validate(provider, tier)
    if media_type not in VALID_MEDIA_TYPES:
        raise InvalidMediaTypeError(
            f"Unknown media_type {media_type!r}. Valid: {VALID_MEDIA_TYPES}"
        )
    if reference_image_url is not None:
        _validate_url(reference_image_url, "reference_image_url")

    model = get_model_id(provider, "generate", media_type, tier)
    if model is UNSUPPORTED:
        raise _unsupported(provider, media_type, "generate")

    mod = _load_provider(provider)
    if media_type == "image":
        return mod.generate_image(prompt, tier, reference_image_url, aspect_ratio)
    return mod.generate_video(
        prompt, tier, reference_image_url, job_id, aspect_ratio, duration_seconds
    )
=======
def dispatch_generate(request: GenerateRequest) -> dict[str, Any]:
    """Dispatch generate call to provider.

    When ``provider`` is ``None``, auto-resolve via :func:`_default_provider`
    (first provider whose API key is present in the environment).
    """
    provider = request.provider
    if provider is None:
        provider = _default_provider()
    _validate(provider, request.tier)
    if request.media_type not in VALID_MEDIA_TYPES:
        raise InvalidMediaTypeError(
            f"Unknown media_type {request.media_type!r}. Valid: {VALID_MEDIA_TYPES}"
        )
    if request.reference_image_url is not None:
        _validate_url(request.reference_image_url, "reference_image_url")

    model = get_model_id(provider, "generate", request.media_type, request.tier)
    if model is UNSUPPORTED:
        raise _unsupported(provider, request.media_type, "generate")

    mod = _load_provider(provider)
    if request.media_type == "image":
        return mod.generate_image(
            request.prompt, request.tier, request.reference_image_url, request.aspect_ratio
        )
    return mod.generate_video(
        request.prompt,
        request.tier,
        request.reference_image_url,
        request.job_id,
        request.aspect_ratio,
        request.duration_seconds,
    )
>>>>>>> REPLACE
