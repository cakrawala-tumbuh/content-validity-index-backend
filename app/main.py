"""Entrypoint aplikasi FastAPI Content Validity Index."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

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
        None
    """
    logger.info("Menjalankan migrasi database...")
    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        command.upgrade(alembic_cfg, "head")
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
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
from app.routers import activity_logs, auth, instruments, ratings, users  # noqa: E402

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
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
