"""
Database module
===============
Database connection and session management
"""

from .session import SessionLocal, engine, Base, get_db
import asyncpg
from ..core.config import settings
from urllib.parse import urlparse
import asyncio

_connection_pool = None
_pool_lock = asyncio.Lock()

async def get_db_connection():
    """
    Async database connection function
    Returns an asyncpg connection from the pool
    
    Usage:
        conn = await get_db_connection()
        try:
            rows = await conn.fetch(query, *args)
        finally:
            await _connection_pool.release(conn)
    """
    global _connection_pool
    
    if _connection_pool is None:
        async with _pool_lock:
            if _connection_pool is None:
                # Parse DATABASE_URL
                # Format: postgresql://user:password@host:port/database
                parsed = urlparse(settings.DATABASE_URL)
                
                _connection_pool = await asyncpg.create_pool(
                    host=parsed.hostname or "localhost",
                    port=parsed.port or 5432,
                    user=parsed.username or "postgres",
                    password=parsed.password or "",
                    database=parsed.path.lstrip("/") or "postgres",
                    min_size=1,
                    max_size=10
                )
    
    # Return a connection from the pool
    conn = await _connection_pool.acquire()
    return conn

__all__ = ["SessionLocal", "engine", "Base", "get_db", "get_db_connection"]
