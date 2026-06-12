"""Router untuk endpoint backup dan restore database (admin only)."""

import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.backup import BackupData, RestoreResponse
from app.services.backup_service import BackupService
from app.utils.activity_logger import log_activity

router = APIRouter(prefix="/backup", tags=["Backup & Restore"])


@router.get(
    "/",
    summary="Unduh backup database",
    description=(
        "Mengekspor seluruh data aplikasi menjadi satu berkas JSON yang dapat diunduh. "
        "Hanya admin. Berkas hasil dapat digunakan kembali pada endpoint restore."
    ),
    responses={
        200: {
            "description": "Berkas backup JSON.",
            "content": {"application/json": {}},
        },
        403: {"description": "Akses ditolak, diperlukan role admin."},
    },
)
async def download_backup(
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Mengekspor dan mengunduh seluruh data database sebagai berkas JSON.

    Args:
        request: HTTP request yang sedang diproses.
        admin: Admin yang melakukan backup.
        db: AsyncSession database.

    Returns:
        Response berisi berkas JSON backup dengan header unduhan.
    """
    service = BackupService(db)
    data = await service.export_data()
    await log_activity(
        db=db,
        action="export_backup",
        request=request,
        user_id=admin.id,
        resource_type="database",
        metadata={"tables": len(data["tables"])},
    )
    await db.commit()

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    filename = f"cvi-backup-{timestamp}.json"
    content = json.dumps(data, ensure_ascii=False, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/restore",
    response_model=RestoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Pulihkan database dari backup",
    description=(
        "Memulihkan seluruh data aplikasi dari berkas backup JSON. **Operasi destruktif:** "
        "seluruh data yang ada akan dihapus dan digantikan oleh data backup. Hanya admin."
    ),
    responses={
        200: {"description": "Restore berhasil."},
        403: {"description": "Akses ditolak, diperlukan role admin."},
        422: {"description": "Format berkas backup tidak valid."},
    },
)
async def restore_backup(
    backup: BackupData,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> RestoreResponse:
    """Memulihkan database dari data backup (admin only).

    Args:
        backup: Data backup hasil endpoint unduh backup.
        request: HTTP request yang sedang diproses.
        admin: Admin yang melakukan restore.
        db: AsyncSession database.

    Returns:
        Ringkasan jumlah baris yang dipulihkan per tabel.
    """
    service = BackupService(db)
    restored = await service.import_data(backup.tables)
    total_rows = sum(restored.values())
    await log_activity(
        db=db,
        action="restore_backup",
        request=request,
        user_id=admin.id,
        resource_type="database",
        metadata={"total_rows": total_rows},
    )
    await db.commit()
    return RestoreResponse(
        message="Restore database berhasil.",
        tables_restored=restored,
        total_rows=total_rows,
    )
