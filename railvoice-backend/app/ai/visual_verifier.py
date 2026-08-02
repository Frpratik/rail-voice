from __future__ import annotations

import io
import logging
from typing import Any

from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.issue import IssuePhoto

logger = logging.getLogger(__name__)


class VisualVerifierService:
    def compute_perceptual_hash(self, data: bytes) -> str:
        """Compute a 64-bit difference hash (dhash) for image tamper & duplicate matching."""
        try:
            img = Image.open(io.BytesIO(data)).convert("L")
            img = img.resize((9, 8), Image.Resampling.LANCZOS)
            pixels = list(img.getdata())

            difference = []
            for row in range(8):
                for col in range(8):
                    pixel_left = pixels[row * 9 + col]
                    pixel_right = pixels[row * 9 + col + 1]
                    difference.append(pixel_left > pixel_right)

            # Convert 64 booleans to 16 hex characters
            decimal_value = 0
            hex_string = []
            for index, value in enumerate(difference):
                if value:
                    decimal_value += 1 << (index % 4)
                if index % 4 == 3:
                    hex_string.append(hex(decimal_value)[2:])
                    decimal_value = 0

            return "".join(hex_string)
        except Exception as exc:
            logger.warning(f"Failed to compute perceptual hash: {exc}")
            import hashlib

            return hashlib.md5(data[:512]).hexdigest()[:16]

    async def verify_upload(
        self, db: AsyncSession, data: bytes
    ) -> tuple[str, str, dict[str, Any]]:
        """Verify image binary data, calculate perceptual hash, and check for duplicates."""
        p_hash = self.compute_perceptual_hash(data)

        # Query database for existing photos with identical perceptual hash
        existing = await db.scalar(
            select(IssuePhoto).where(IssuePhoto.perceptual_hash == p_hash).limit(1)
        )

        flags: dict[str, Any] = {"perceptual_hash": p_hash}
        if existing:
            flags["duplicate_detected"] = True
            flags["original_photo_id"] = str(existing.id)
            scan_status = "flagged_duplicate"
        else:
            flags["duplicate_detected"] = False
            scan_status = "passed"

        return p_hash, scan_status, flags


visual_verifier = VisualVerifierService()
