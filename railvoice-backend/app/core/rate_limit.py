from __future__ import annotations

import logging
import time
from collections import defaultdict
from threading import Lock

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class MemoryRateLimitBackend:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def hit(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int, int, int]:
        now = time.time()
        with self._lock:
            bucket = [t for t in self._hits[key] if now - t < window_seconds]
            if len(bucket) >= limit:
                self._hits[key] = bucket
                retry_after = max(1, int(window_seconds - (now - bucket[0]))) if bucket else window_seconds
                return False, limit, 0, retry_after
            bucket.append(now)
            self._hits[key] = bucket
            remaining = max(0, limit - len(bucket))
            return True, limit, remaining, 0


class RedisRateLimitBackend:
    def __init__(self, redis_url: str) -> None:
        import redis

        self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        self._client.ping()

    def hit(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int, int, int]:
        window = int(time.time()) // window_seconds
        redis_key = f"rl:{key}:{window}"
        pipe = self._client.pipeline()
        pipe.incr(redis_key)
        pipe.expire(redis_key, window_seconds + 1)
        count, _ = pipe.execute()
        count = int(count)
        if count > limit:
            ttl = self._client.ttl(redis_key)
            retry_after = ttl if isinstance(ttl, int) and ttl > 0 else window_seconds
            return False, limit, 0, retry_after
        return True, limit, max(0, limit - count), 0


_memory = MemoryRateLimitBackend()
_redis: RedisRateLimitBackend | None = None
_redis_failed = False


def _get_backend() -> tuple[MemoryRateLimitBackend | RedisRateLimitBackend, bool]:
    global _redis, _redis_failed
    if not settings.use_redis_rate_limit:
        return _memory, False

    if _redis_failed:
        return _memory, True

    if _redis is None:
        url = settings.redis_url_effective
        if not url:
            return _memory, True
        try:
            _redis = RedisRateLimitBackend(url)
        except Exception as exc:
            logger.warning("Redis rate limit unavailable, falling back to memory: %s", exc)
            _redis_failed = True
            return _memory, True
    return _redis, False


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _rate_limited_response(max_limit: int, retry_after: int) -> JSONResponse:
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
            "Retry-After": str(retry_after),
        },
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled or request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        client = _client_key(request)
        limit = settings.rate_limit_default_per_minute
        key = f"read:{client}"
        window = 60
        is_otp = path.endswith("/auth/otp/request")

        if is_otp:
            limit = settings.effective_otp_per_minute
            key = f"otp:{client}"
        elif request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            limit = settings.rate_limit_write_per_minute
            key = f"write:{client}"

        backend, redis_degraded = _get_backend()

        if (
            is_otp
            and settings.is_production
            and settings.rate_limit_require_redis_in_production
            and redis_degraded
        ):
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "RATE_LIMIT_UNAVAILABLE",
                        "message": "Authentication temporarily unavailable. Please retry shortly.",
                    }
                },
            )

        try:
            allowed, max_limit, remaining, retry_after = backend.hit(key, limit, window)
        except Exception as exc:
            logger.warning("Rate limit backend error: %s", exc)
            if is_otp and settings.is_production and settings.rate_limit_require_redis_in_production:
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_UNAVAILABLE",
                            "message": "Authentication temporarily unavailable. Please retry shortly.",
                        }
                    },
                )
            allowed, max_limit, remaining, retry_after = _memory.hit(key, limit, window)

        if not allowed:
            return _rate_limited_response(max_limit, retry_after)

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


def check_mobile_otp_limit(mobile_hash: str) -> tuple[bool, int]:
    """Per-mobile hourly OTP request limit. Returns (allowed, retry_after)."""
    backend, _ = _get_backend()
    key = f"mobile:otp:{mobile_hash}"
    allowed, _, _, retry_after = backend.hit(
        key,
        settings.effective_otp_per_mobile_per_hour,
        window_seconds=3600,
    )
    return allowed, retry_after


def ping_redis_for_startup() -> str | None:
    """Return error message if production requires Redis and it is unreachable."""
    if not settings.is_production or not settings.rate_limit_require_redis_in_production:
        return None
    url = settings.redis_url_effective
    if not url:
        return "REDIS_URL is required in production"
    try:
        RedisRateLimitBackend(url)
    except Exception as exc:
        return f"REDIS_URL unreachable: {exc}"
    return None
