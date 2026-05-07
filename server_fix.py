<<<<<<< SEARCH
from imagine_mcp.dispatcher import dispatch_generate, dispatch_understand
=======
from imagine_mcp.dispatcher import GenerateRequest, dispatch_generate, dispatch_understand
>>>>>>> REPLACE
<<<<<<< SEARCH
    def generate(
        media_type: Literal["image", "video"],
        prompt: str,
        provider: str | None = None,
        tier: str = "poor",
        reference_image_url: str | None = None,
        job_id: str | None = None,
        output_mode: Literal["base64", "path", "both"] = "both",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
    ) -> dict[str, Any]:
        """Generate image or video."""
        return dispatch_generate(
            media_type,
            prompt,
            provider,
            tier,
            reference_image_url,
            job_id,
            aspect_ratio,
            duration_seconds,
        )
=======
    def generate(
        media_type: Literal["image", "video"],
        prompt: str,
        provider: str | None = None,
        tier: str = "poor",
        reference_image_url: str | None = None,
        job_id: str | None = None,
        output_mode: Literal["base64", "path", "both"] = "both",
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
    ) -> dict[str, Any]:
        """Generate image or video."""
        return dispatch_generate(
            GenerateRequest(
                media_type=media_type,
                prompt=prompt,
                provider=provider,
                tier=tier,
                reference_image_url=reference_image_url,
                job_id=job_id,
                aspect_ratio=aspect_ratio,
                duration_seconds=duration_seconds,
            )
        )
>>>>>>> REPLACE
