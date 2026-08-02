from __future__ import annotations

import json
import logging
import time
from threading import Lock
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class MemoryIdempotencyCache:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, int, bytes]] = {}
        self._lock = Lock()

    def get(self, key: str) -> tuple[int, bytes] | None:
        now = time.time()
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            expire_at, status_code, content = entry
            if now > expire_at:
                del self._cache[key]
                return None
            return status_code, content

    def set(self, key: str, status_code: int, content: bytes, ttl_seconds: int = 86400) -> None:
        now = time.time()
        with self._lock:
            # Clean expired items if cache grows large
            if len(self._cache) > 2000:
                expired = [k for k, (exp, _, _) in self._cache.items() if now > exp]
                for k in expired:
                    del self._cache[k]
            self._cache[key] = (now + ttl_seconds, status_code, content)


_memory_idempotency_cache = MemoryIdempotencyCache()


def _get_redis_client():
    if not settings.redis_url_effective:
        return None
    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url_effective, decode_responses=False)
        return client
    except Exception:
        return None


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key") or request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        cache_key = f"idempotency:{idempotency_key.strip()}"
        cached = self._get_cached_response(cache_key)
        if cached:
            status_code, content = cached
            return Response(
                content=content,
                status_code=status_code,
                media_type="application/json",
                headers={"X-Idempotency-Hit": "true"},
            )

        response = await call_next(request)

        # Only cache successful write responses under 100KB
        if 200 <= response.status_code < 300:
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk if isinstance(chunk, bytes) else chunk.encode("utf-8")

            if len(body_bytes) <= 100 * 1024:
                self._set_cached_response(cache_key, response.status_code, body_bytes)

            headers = dict(response.headers)
            headers.pop("content-length", None)
            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type,
            )

        return response

    def _get_cached_response(self, cache_key: str) -> tuple[int, bytes] | None:
        redis_client = _get_redis_client()
        if redis_client:
            try:
                raw = redis_client.get(cache_key)
                if raw:
                    data = json.loads(raw.decode("utf-8"))
                    return data["status_code"], data["content"].encode("utf-8")
            except Exception as exc:
                logger.warning(f"Redis idempotency lookup failed: {exc}")

        return _memory_idempotency_cache.get(cache_key)

    def _set_cached_response(self, cache_key: str, status_code: int, content: bytes) -> None:
        redis_client = _get_redis_client()
        if redis_client:
            try:
                payload = json.dumps(
                    {"status_code": status_code, "content": content.decode("utf-8", errors="ignore")}
                )
                redis_client.setex(cache_key, 86400, payload)
                return
            except Exception as exc:
                logger.warning(f"Redis idempotency save failed: {exc}")

        _memory_idempotency_cache.set(cache_key, status_code, content)
