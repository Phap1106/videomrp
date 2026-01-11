from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from contextlib import contextmanager

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings


def _build_urls(raw_url: str) -> tuple[str, str]:
    """
    Build (sync_url, async_url) from a single DATABASE_URL.
    Supports:
      - Postgres: psycopg2 <-> asyncpg
      - MySQL: pymysql <-> aiomysql
    Accepts raw_url being either sync or async; derives the other.
    """
    url = (raw_url or "").strip()
    if not url:
        raise ValueError("DATABASE_URL is empty")

    # --- Postgres ---
    if url.startswith("postgresql+asyncpg://"):
        sync_url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        return sync_url, url

    if url.startswith("postgresql+psycopg2://"):
        async_url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        return url, async_url

    if url.startswith("postgresql://"):
        # Default sync for create_engine, derive explicit async form
        async_url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url, async_url

    # --- MySQL ---
    if url.startswith("mysql+aiomysql://"):
        sync_url = url.replace("mysql+aiomysql://", "mysql+pymysql://", 1)
        return sync_url, url

    if url.startswith("mysql+pymysql://"):
        async_url = url.replace("mysql+pymysql://", "mysql+aiomysql://", 1)
        return url, async_url

    if url.startswith("mysql://"):
        sync_url = url.replace("mysql://", "mysql+pymysql://", 1)
        async_url = url.replace("mysql://", "mysql+aiomysql://", 1)
        return sync_url, async_url

    # Fallback: treat as sync and keep async same (best-effort)
    return url, url


SYNC_DATABASE_URL, ASYNC_DATABASE_URL = _build_urls(settings.DATABASE_URL)

# --------------------
# Sync (default) DB
# --------------------
engine = create_engine(
    SYNC_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=bool(getattr(settings, "DEBUG", False)),
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions (sync)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# --------------------
# Async DB (optional)
# --------------------
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=bool(getattr(settings, "DEBUG", False)),
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
