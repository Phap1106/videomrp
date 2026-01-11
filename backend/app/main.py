import os
import time
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.core.logger import logger
from sqlalchemy import text

from app.api.endpoints import api_router
from app.core.config import settings
from app.core.logger import setup_logging
from app.database import Base, SessionLocal, engine
from app.utils.file_utils import ensure_dirs


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Create DB tables (sync engine) - run in thread to avoid blocking
    try:
        await anyio.to_thread.run_sync(lambda: Base.metadata.create_all(bind=engine))
        logger.info("✅ Database tables created")
    except Exception as e:
        logger.error(f"❌ Database error: {e}")

    # Ensure directories exist
    try:
        ensure_dirs()
        logger.info("✅ Directories created")
    except Exception as e:
        logger.error(f"❌ Directory error: {e}")

    yield
    logger.info("👋 Shutting down...")


setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered video reuploading tool for TikTok, YouTube, Facebook, Instagram, Douyin",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start_time)
    return response


if os.path.exists("data/processed"):
    app.mount("/processed", StaticFiles(directory="data/processed"), name="processed")

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/api/health",
        "status": "running",
    }


@app.get("/api/health")
async def health_check():
    from redis import Redis

    checks = {"api": True, "database": False, "redis": False, "storage": False}

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    try:
        redis_client = Redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        checks["redis"] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")

    if os.path.exists("data") and os.access("data", os.W_OK):
        checks["storage"] = True

    status_code = 200 if all(checks.values()) else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if all(checks.values()) else "unhealthy",
            "checks": checks,
            "timestamp": time.time(),
            "version": settings.APP_VERSION,
        },
    )
