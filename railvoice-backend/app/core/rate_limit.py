from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


class _MemoryBucket:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def hit(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int, int]:
        now = time.time()
        with self._lock:
            bucket = [t for t in self._hits[key] if now - t < window_seconds]
            remaining = max(0, limit - len(bucket))
            if len(bucket) >= limit:
                self._hits[key] = bucket
                return False, limit, remaining
            bucket.append(now)
            self._hits[key] = bucket
            return True, limit, max(0, limit - len(bucket))


_memory = _MemoryBucket()


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled or request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        key = _client_key(request)
        limit = settings.rate_limit_default_per_minute

        if path.endswith("/auth/otp/request"):
            limit = settings.rate_limit_otp_per_minute
            key = f"otp:{key}"
        elif request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            limit = settings.rate_limit_write_per_minute
            key = f"write:{key}"
        else:
            key = f"read:{key}"

        allowed, max_limit, remaining = _memory.hit(key, limit)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests. Please retry shortly.",
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(max_limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60",
                },
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
