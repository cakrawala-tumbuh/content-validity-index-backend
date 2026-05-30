"""Fixtures pytest untuk test suite CVI backend."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db() -> AsyncSession:  # type: ignore[override]
    """Fixture AsyncSession yang terhubung ke SQLite in-memory untuk test.

    Yields:
        AsyncSession yang sudah memiliki skema tabel lengkap.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncClient:  # type: ignore[override]
    """Fixture AsyncClient dengan dependency get_db di-override ke test DB.

    Args:
        db: AsyncSession dari fixture `db`.

    Yields:
        AsyncClient yang siap digunakan untuk integration test.
    """
    async def override_get_db() -> AsyncSession:  # type: ignore[override]
        """Override dependency get_db untuk menggunakan test DB."""
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
