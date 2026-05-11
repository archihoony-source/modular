"""Supabase Postgres 커넥션 풀 관리.

psycopg v3 async 연결 풀 사용.
"""

from typing import AsyncIterator

from psycopg_pool import AsyncConnectionPool

from app.config import settings

_pool: AsyncConnectionPool | None = None


async def init_db_pool() -> None:
    """앱 시작 시 1회 호출."""
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=5,         # 무료 티어 부담 최소화
            open=False,
        )
        await _pool.open()


async def close_db_pool() -> None:
    """앱 종료 시 호출."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized.")
    return _pool


async def get_connection() -> AsyncIterator:
    """FastAPI Depends용 (선택 사용)."""
    pool = await get_pool()
    async with pool.connection() as conn:
        yield conn
