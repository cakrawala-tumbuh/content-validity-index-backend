"""Utilitas untuk mencatat aktivitas pengguna ke database."""

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.repositories.activity_log_repository import ActivityLogRepository


async def log_activity(
    db: AsyncSession,
    action: str,
    request: Request,
    user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Mencatat satu entri aktivitas pengguna ke database.

    Dipanggil dari router atau service setelah operasi berhasil dilakukan.
    Kegagalan pencatatan log tidak boleh membatalkan operasi utama.

    Args:
        db: AsyncSession database yang aktif.
        action: Nama aksi yang dilakukan (contoh: 'login', 'create_instrument').
        request: HTTP request yang sedang diproses.
        user_id: ID pengguna yang melakukan aksi (opsional).
        resource_type: Tipe resource yang dioperasikan (opsional).
        resource_id: ID resource yang dioperasikan (opsional).
        metadata: Informasi tambahan dalam format dict (opsional).
    """
    import uuid

    ip_address = "unknown"
    if request.client:
        ip_address = request.client.host

    log = ActivityLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent"),
        metadata_=metadata,
    )

    repo = ActivityLogRepository(db)
    await repo.create(log)
