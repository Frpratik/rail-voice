from __future__ import annotations

import asyncio
import mimetypes
import uuid
from pathlib import Path

import aiofiles

from app.core.config import settings


class StorageService:
    """Local or S3-compatible object storage."""

    def __init__(self) -> None:
        self.root = Path(settings.local_storage_path)
        self.root.mkdir(parents=True, exist_ok=True)
        self._s3 = None

    @property
    def backend(self) -> str:
        return (settings.storage_backend or "local").lower().strip()

    def build_key(self, *, issue_id: uuid.UUID, filename: str) -> str:
        safe = filename.replace("/", "_").replace("\\", "_")
        return f"issues/{issue_id}/{uuid.uuid4().hex}_{safe}"

    def _get_s3(self):
        if self._s3 is not None:
            return self._s3
        import boto3
        from botocore.config import Config

        kwargs: dict = {
            "service_name": "s3",
            "aws_access_key_id": settings.s3_access_key or None,
            "aws_secret_access_key": settings.s3_secret_key or None,
            "region_name": settings.s3_region or "ap-south-1",
            "config": Config(signature_version="s3v4"),
        }
        if settings.s3_endpoint:
            kwargs["endpoint_url"] = settings.s3_endpoint
        self._s3 = boto3.client(**kwargs)
        return self._s3

    async def save_bytes(self, key: str, data: bytes, content_type: str | None = None) -> str:
        if self.backend == "s3":
            return await asyncio.to_thread(self._s3_put, key, data, content_type)
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)
        return key

    def _s3_put(self, key: str, data: bytes, content_type: str | None) -> str:
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET is required when STORAGE_BACKEND=s3")
        extra = {"ContentType": content_type or "application/octet-stream"}
        self._get_s3().put_object(Bucket=settings.s3_bucket, Key=key, Body=data, **extra)
        return key

    def public_url(self, key: str) -> str:
        if self.backend == "s3":
            base = (settings.s3_public_base_url or "").rstrip("/")
            if base:
                return f"{base}/{key}"
            if settings.s3_endpoint:
                return f"{settings.s3_endpoint.rstrip('/')}/{settings.s3_bucket}/{key}"
            return f"https://{settings.s3_bucket}.s3.{settings.s3_region}.amazonaws.com/{key}"
        return f"{settings.public_base_url.rstrip('/')}/media/{key}"

    def resolve_path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not str(path).startswith(str(self.root.resolve())):
            raise ValueError("Invalid storage key")
        return path

    def guess_mime(self, filename: str) -> str:
        mime, _ = mimetypes.guess_type(filename)
        return mime or "application/octet-stream"

    def validate_image_bytes(self, data: bytes) -> str:
        """Validate binary magic bytes using Pillow. Returns canonical mime_type (e.g. 'image/jpeg')."""
        import io
        from PIL import Image

        if not data or len(data) < 12:
            raise ValueError("File is empty or corrupted")

        if len(data) > 10 * 1024 * 1024:
            raise ValueError("File exceeds maximum allowed size of 10MB")

        try:
            img = Image.open(io.BytesIO(data))
            img.verify()
            fmt = (img.format or "").upper()
            format_mime_map = {
                "JPEG": "image/jpeg",
                "JPG": "image/jpeg",
                "PNG": "image/png",
                "WEBP": "image/webp",
                "GIF": "image/gif",
            }
            mime = format_mime_map.get(fmt)
            if not mime:
                raise ValueError(f"Unsupported image format: {fmt}. Allowed: JPEG, PNG, WebP, GIF.")
            return mime
        except Exception as exc:
            if isinstance(exc, ValueError):
                raise
            raise ValueError("Invalid image format or corrupted binary data") from exc


storage_service = StorageService()
