from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path

import aiofiles

from app.core.config import settings


class StorageService:
    """Local filesystem storage with S3-shaped interface for later swap."""

    def __init__(self) -> None:
        self.root = Path(settings.local_storage_path)
        self.root.mkdir(parents=True, exist_ok=True)

    def build_key(self, *, issue_id: uuid.UUID, filename: str) -> str:
        safe = filename.replace("/", "_").replace("\\", "_")
        return f"issues/{issue_id}/{uuid.uuid4().hex}_{safe}"

    async def save_bytes(self, key: str, data: bytes, content_type: str | None = None) -> str:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)
        return key

    def public_url(self, key: str) -> str:
        return f"{settings.public_base_url.rstrip('/')}/media/{key}"

    def resolve_path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not str(path).startswith(str(self.root.resolve())):
            raise ValueError("Invalid storage key")
        return path

    def guess_mime(self, filename: str) -> str:
        mime, _ = mimetypes.guess_type(filename)
        return mime or "application/octet-stream"


storage_service = StorageService()
