"""
Database engine, session factory, and initialization.

The daemon uses async SQLAlchemy with aiosqlite as the driver. This gives us:
- Non-blocking DB calls that play nice with ib_async's asyncio loop
- A path to PostgreSQL later — same code, different connection string
- Idempotent table creation on startup via init_db()

Usage:

    from daemon.persistence import get_session, Deployment

    async with get_session() as session:
        session.add(Deployment(...))
        # auto-commits on context exit, auto-rolls-back on exception
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


# Connection string. Defaults to a local SQLite file alongside the daemon.
# Override with the DATABASE_URL env var when running on the VPS or in tests.
#
# Examples:
#   sqlite+aiosqlite:///./trading.db                          (local dev)
#   sqlite+aiosqlite:////var/lib/algo-lab/trading.db          (VPS, absolute path)
#   postgresql+asyncpg://user:pass@host:5432/algolab          (future, postgres)
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./trading.db",
)


engine = create_async_engine(
    DATABASE_URL,
    echo=False,           # set True for SQL query logging while debugging
    pool_pre_ping=True,   # checks connection health before each use
)


async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,   # let objects stay usable after commit
    class_=AsyncSession,
)


async def init_db() -> None:
    """
    Create all tables if they don't exist. Idempotent — safe to call on
    every daemon startup.

    For schema migrations after the first version, use Alembic instead.
    """
    # Late import to avoid circular dep at module load time.
    from daemon.persistence.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """
    Context-managed async session. Commits on clean exit, rolls back on
    exception. Use this for any code path that writes to the database.

    For read-only queries you can use it the same way — the empty commit
    on exit is a no-op when nothing was changed.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    """Dispose of the engine's connection pool. Call on daemon shutdown."""
    await engine.dispose()
