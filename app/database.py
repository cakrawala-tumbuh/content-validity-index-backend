"""Koneksi dan session factory untuk database async SQLAlchemy."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

_settings = get_settings()

engine = create_async_engine(
    _settings.DATABASE_URL,
    echo=_settings.APP_ENV == "development",
)

AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency untuk mendapatkan async database session.

    Setiap request mendapatkan session baru. Session di-commit otomatis
    di akhir request yang sukses, di-rollback jika terjadi exception.

    Yields:
        AsyncSession: Session SQLAlchemy yang aktif.

    Raises:
        Exception: Meneruskan kembali (re-raise) exception apa pun yang terjadi
            selama request setelah session di-rollback.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
