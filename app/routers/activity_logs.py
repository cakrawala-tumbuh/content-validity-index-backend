"""Router untuk endpoint log aktivitas pengguna."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.activity_log import ActivityLogResponse
from app.services.activity_log_service import ActivityLogService

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


@router.get(
    "/",
    response_model=list[ActivityLogResponse],
    summary="Daftar log aktivitas",
    description=(
        "Mengambil log aktivitas semua pengguna dengan opsi filter. Hanya admin. "
        "Log diurutkan dari yang terbaru."
    ),
    responses={
        403: {"description": "Akses ditolak, diperlukan role admin."},
    },
)
async def list_activity_logs(
    user_id: str | None = None,
    action: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ActivityLogResponse]:
    """Mengambil daftar log aktivitas dengan filter opsional (admin only).

    Args:
        user_id: Filter berdasarkan ID pengguna tertentu.
        action: Filter berdasarkan nama aksi (contoh: 'login', 'create_instrument').
        start_date: Batas awal tanggal/waktu log.
        end_date: Batas akhir tanggal/waktu log.
        skip: Jumlah record yang dilewati (pagination).
        limit: Jumlah maksimal record yang dikembalikan.
        _admin: Dependency yang memvalidasi role admin.
        db: AsyncSession database.

    Returns:
        Daftar log aktivitas yang sesuai filter.
    """
    service = ActivityLogService(db)
    logs = await service.get_all(
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return [ActivityLogResponse.model_validate(log) for log in logs]
