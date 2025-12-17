"""
Neon Serverless Postgres connection pool management.

Uses psycopg3 AsyncConnectionPool for efficient connection pooling.
"""

import logging
from typing import Optional

from psycopg_pool import AsyncConnectionPool

from app.config import settings

logger = logging.getLogger(__name__)

# Global connection pool singleton
_pool: Optional[AsyncConnectionPool] = None


async def get_neon_pool() -> AsyncConnectionPool:
    """
    Get or create the Neon Postgres connection pool.

    Returns:
        AsyncConnectionPool: Configured connection pool

    Raises:
        RuntimeError: If pool initialization fails
    """
    global _pool

    if _pool is None:
        try:
            _pool = AsyncConnectionPool(
                conninfo=settings.db_url,  # Use db_url property that supports both neon_db_url and database_url
                min_size=5,
                max_size=20,
                timeout=30,
                open=False,  # Don't open immediately
            )
            await _pool.open()
            logger.info("Neon Postgres connection pool initialized (min=5, max=20)")
        except Exception as e:
            logger.error(f"Failed to initialize Neon connection pool: {e}")
            raise RuntimeError(f"Neon connection pool initialization failed: {e}")

    return _pool


async def close_neon_pool() -> None:
    """Close the Neon Postgres connection pool."""
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Neon Postgres connection pool closed")


async def check_neon_health() -> bool:
    """
    Check if Neon Postgres connection is healthy.

    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        pool = await get_neon_pool()
        async with pool.connection() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Neon health check failed: {e}")
        return False
