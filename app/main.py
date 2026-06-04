"""Entrypoint aplikasi FastAPI Content Validity Index."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Kelola lifecycle aplikasi: jalankan migrasi saat startup.

    Args:
        app: Instance FastAPI.

    Yields:
        None: Kontrol dikembalikan ke aplikasi selama masa hidupnya.

    Raises:
        Exception: Bila migrasi database gagal saat startup; exception
            di-log lalu di-raise ulang sehingga aplikasi tidak ikut berjalan.
    """
    logger.info("Menjalankan migrasi database...")
    try:
        from alembic.config import Config

        from alembic import command

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

        # Jalankan di thread pool agar tidak memblokir event loop Uvicorn.
        # Di thread pool, tidak ada running loop, sehingga alembic/env.py
        # mengambil path asyncio.run() yang bersih — menghindari deadlock.
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: command.upgrade(alembic_cfg, "head"))
        logger.info("Migrasi database selesai.")
    except Exception as exc:
        logger.error("Gagal menjalankan migrasi: %s", exc)
        raise
    yield
    logger.info("Aplikasi berhenti.")


app = FastAPI(
    title="Content Validity Index API",
    description=(
        "REST API untuk pengelolaan **Content Validity Index (CVI)**. "
        "Mendukung pengelolaan instrumen, penilaian expert, "
        "kalkulasi I-CVI/S-CVI, dan ekspor ke Excel."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Proxy headers — hormati X-Forwarded-Proto/For dari reverse proxy (Traefik).
# Ditambahkan terakhir agar menjadi lapisan terluar: skema request (https) dikoreksi
# sebelum routing sehingga redirect trailing-slash memakai https dan tidak menstrip
# header Authorization saat di-follow oleh klien.
app.add_middleware(
    ProxyHeadersMiddleware,
    trusted_hosts=settings.FORWARDED_ALLOW_IPS,
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Tangani exception yang tidak tertangani tanpa mengekspos stack trace.

    Args:
        request: HTTP request yang menyebabkan exception.
        exc: Exception yang tidak tertangani.

    Returns:
        JSONResponse dengan pesan error generik.
    """
    logger.exception("Unhandled exception pada %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Terjadi kesalahan internal server."},
    )


# Import router setelah app dibuat untuk menghindari circular import
from app.routers import (  # noqa: E402
    activity_logs,
    auth,
    expertise_areas,
    instruments,
    ratings,
    users,
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(expertise_areas.router, prefix="/api/v1")
app.include_router(instruments.router, prefix="/api/v1")
app.include_router(ratings.router, prefix="/api/v1")
app.include_router(activity_logs.router, prefix="/api/v1")


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Endpoint untuk memeriksa status aplikasi.",
)
async def health_check() -> dict[str, str]:
    """Mengembalikan status kesehatan aplikasi.

    Returns:
        Dict dengan status aplikasi.
    """
    return {"status": "ok"}
