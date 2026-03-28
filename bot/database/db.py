"""Async PostgreSQL database manager using SQLAlchemy 2.0."""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models import Base

logger = logging.getLogger(__name__)


class Database:
    """Manages the async database engine and session factory lifecycle."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._engine = None
        self._session_factory: Optional[async_sessionmaker] = None

    async def connect(self) -> None:
        """Create the async engine and auto-create all ORM tables."""
        self._engine = create_async_engine(self.url, echo=False, pool_pre_ping=True)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database connected: %s", self.url.split("@")[-1])

    async def disconnect(self) -> None:
        """Dispose of the connection pool gracefully."""
        if self._engine is not None:
            await self._engine.dispose()
            logger.info("Database disconnected.")

    def get_session(self) -> AsyncSession:
        """Return a new :class:`AsyncSession` usable as an async context manager."""
        if self._session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._session_factory()
