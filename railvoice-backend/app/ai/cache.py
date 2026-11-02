"""Small in-memory cache for AI output, so repeated views don't repeat paid requests."""

from __future__ import annotations

import time
from typing import Any

from app.core.config import settings

_store: dict[str, tuple[float, Any]] = {}
_MAX_ENTRIES = 2000


def get(key: str) -> Any | None:
    hit = _store.get(key)
    if not hit:
        return None
    expires, value = hit
    if expires < time.monotonic():
        _store.pop(key, None)
        return None
    return value


def put(key: str, value: Any, *, hours: float | None = None) -> None:
    if len(_store) >= _MAX_ENTRIES:
        # Drop the entries closest to expiry.
        for old in sorted(_store, key=lambda k: _store[k][0])[: _MAX_ENTRIES // 10]:
            _store.pop(old, None)
    ttl = (hours if hours is not None else settings.ai_cache_hours) * 3600
    _store[key] = (time.monotonic() + ttl, value)


def clear() -> None:
    _store.clear()
