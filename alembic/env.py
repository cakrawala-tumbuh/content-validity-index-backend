"""Konfigurasi Alembic untuk migrasi database async."""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.config import get_settings

# Import semua model agar autogenerate bisa mendeteksinya
from app.models import Base  # noqa: F401

config = context.config
fileConfig(config.config_file_name)  # type: ignore[arg-type]

target_metadata = Base.metadata

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Menjalankan migrasi dalam mode offline (tanpa koneksi DB live).

    Mode offline berguna untuk menghasilkan SQL script tanpa memerlukan
    koneksi database yang aktif.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Menjalankan migrasi dengan koneksi database yang sudah ada.

    Args:
        connection: Koneksi SQLAlchemy yang aktif.
    """
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Menjalankan migrasi dalam mode async (mode utama untuk aplikasi ini)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point untuk menjalankan migrasi online (async).

    Menangani dua kasus:
    1. Dipanggil dari CLI — tidak ada event loop yang berjalan.
    2. Dipanggil dari dalam lifespan FastAPI — sudah ada event loop uvicorn.
    """
    import concurrent.futures

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # Tidak ada event loop yang berjalan (CLI mode)
        asyncio.run(run_async_migrations())
    else:
        # Sudah ada event loop (dipanggil dari FastAPI lifespan),
        # jalankan di thread terpisah dengan event loop baru
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, run_async_migrations())
            future.result()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
