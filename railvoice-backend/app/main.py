from contextlib import asynccontextmanager
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.idempotency import IdempotencyMiddleware
from app.core.logging_config import correlation_id_var, setup_logging
from app.core.rate_limit import RateLimitMiddleware, ping_redis_for_startup

setup_logging()

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)
    errors = settings.validate_for_runtime()
    redis_error = ping_redis_for_startup()
    if redis_error:
        errors.append(redis_error)
    if errors:
        raise RuntimeError("Unsafe production configuration: " + "; ".join(errors))
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.3.0",
    description="AI-powered public issue reporting for Indian Railways",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.middleware("http")
async def metrics_and_correlation(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    correlation_id = request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    correlation_id_var.set(correlation_id)
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    endpoint = request.url.path
    REQUEST_LATENCY.labels(request.method, endpoint).observe(duration)
    REQUEST_COUNT.labels(request.method, endpoint, str(response.status_code)).inc()
    response.headers["X-Correlation-Id"] = correlation_id
    return response


app.add_middleware(IdempotencyMiddleware)
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Authorization",
        "Content-Type",
        "Origin",
        "X-Anonymous-Session",
        "X-Correlation-Id",
        "X-Requested-With",
        "Idempotency-Key",
    ],
    expose_headers=["X-Correlation-Id", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=600,
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "correlation_id": getattr(request.state, "correlation_id", None),
            }
        },
    )


app.include_router(api_router, prefix=settings.api_v1_prefix)

media_root = Path(settings.local_storage_path)
media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_root)), name="media")


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}


@app.get("/health/ready")
async def readiness():
    from sqlalchemy import text

    from app.db.session import async_session_factory

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(exc)})


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
