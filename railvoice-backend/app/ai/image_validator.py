from __future__ import annotations

from dataclasses import dataclass

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 10 * 1024 * 1024


@dataclass
class ImageValidationResult:
    is_valid: bool
    relevance_score: float
    flags: list[str]


class ImageValidator:
    """Basic image validation — MIME/size checks; NSFW/deepfake via external API later."""

    def validate(
        self,
        *,
        mime_type: str,
        file_size_bytes: int,
        issue_description: str | None = None,
    ) -> ImageValidationResult:
        flags: list[str] = []
        if mime_type not in ALLOWED_MIME:
            flags.append("invalid_mime")
        if file_size_bytes > MAX_BYTES:
            flags.append("file_too_large")
        if file_size_bytes < 1024:
            flags.append("suspiciously_small")

        is_valid = not flags
        relevance = 0.75 if is_valid else 0.2
        if issue_description and len(issue_description) > 50:
            relevance = min(relevance + 0.1, 0.95)

        return ImageValidationResult(
            is_valid=is_valid,
            relevance_score=round(relevance, 4),
            flags=flags,
        )


image_validator = ImageValidator()
