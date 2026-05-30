"""Repository untuk operasi database entitas ActivityLog."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog


class ActivityLogRepository:
    """Repository untuk operasi pada tabel activity_logs.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi ActivityLogRepository.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: str | None = None,
        action: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[ActivityLog]:
        """Mengambil activity log dengan filter opsional.

        Args:
            skip: Jumlah record yang dilewati.
            limit: Jumlah maksimal record yang dikembalikan.
            user_id: Filter berdasarkan ID pengguna (opsional).
            action: Filter berdasarkan nama aksi (opsional).
            start_date: Filter log setelah tanggal ini (opsional).
            end_date: Filter log sebelum tanggal ini (opsional).

        Returns:
            Daftar ActivityLog sesuai filter, diurutkan terbaru dulu.
        """
        query = select(ActivityLog)
        if user_id:
            query = query.where(ActivityLog.user_id == user_id)
        if action:
            query = query.where(ActivityLog.action == action)
        if start_date:
            query = query.where(ActivityLog.created_at >= start_date)
        if end_date:
            query = query.where(ActivityLog.created_at <= end_date)
        query = query.order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, log: ActivityLog) -> ActivityLog:
        """Menyimpan entri log baru ke database.

        Args:
            log: Instance ActivityLog yang akan disimpan.

        Returns:
            Instance ActivityLog yang sudah disimpan.
        """
        self.db.add(log)
        await self.db.flush()
        return log
