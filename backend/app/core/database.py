"""
Database configuration and session management.
Uses SQLAlchemy 2.0+ with async support for PostgreSQL.
"""

import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base, DeclarativeBase
from sqlalchemy import event, text

from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)

# Create declarative base for ORM models
class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Global engine instance (initialized on startup)
_engine: Optional[AsyncEngine] = None
_async_session_maker: Optional[async_sessionmaker] = None


async def init_database() -> None:
    """
    Initialize database connection pool and create tables.
    Call this during application startup.
    """
    global _engine, _async_session_maker
    
    logger.info("Initializing database connection...")
    
    # Create async engine with connection pooling
    _engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,  # Log SQL queries in debug mode
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,   # Recycle connections after 1 hour
        connect_args={
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
    }
    )
    
    # Test connection
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise
    
    # Create session maker
    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Prevent expired attribute errors
    )
    
    # Create all tables (in production, use Alembic migrations instead)
    if settings.ENVIRONMENT == "development":
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    
    logger.info("Database initialization complete")


async def close_database() -> None:
    """Close database connection pool. Call during application shutdown."""
    global _engine
    
    if _engine:
        logger.info("Closing database connections...")
        await _engine.dispose()
        logger.info("Database connections closed")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database sessions.
    Yields a session and ensures it's closed after use.
    
    Usage:
        async def my_route(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_engine() -> AsyncEngine:
    """Get the database engine instance."""
    if _engine is None:
        raise RuntimeError("Database not initialized")
    return _engine


def get_session_maker() -> async_sessionmaker:
    """Get the async session maker instance."""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized")
    return _async_session_maker