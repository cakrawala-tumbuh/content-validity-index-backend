"""Service untuk pengelolaan log aktivitas pengguna."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.repositories.activity_log_repository import ActivityLogRepository


class ActivityLogService:
    """Service untuk membaca log aktivitas dari database.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi ActivityLogService.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.repo = ActivityLogRepository(db)

    async def get_all(
        self,
        user_id: str | None = None,
        action: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ActivityLog]:
        """Mengambil daftar log aktivitas dengan filter opsional.

        Args:
            user_id: Filter berdasarkan ID pengguna.
            action: Filter berdasarkan nama aksi.
            start_date: Batas awal tanggal/waktu.
            end_date: Batas akhir tanggal/waktu.
            skip: Jumlah record yang dilewati.
            limit: Jumlah maksimal record yang dikembalikan.

        Returns:
            Daftar log aktivitas diurutkan dari yang terbaru.
        """
        return await self.repo.get_all(
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
