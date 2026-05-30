"""Repository untuk operasi database entitas Instrument."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instrument import Instrument


class InstrumentRepository:
    """Repository untuk operasi CRUD pada tabel instruments.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi InstrumentRepository.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db

    async def get_by_id(self, instrument_id: str) -> Instrument | None:
        """Mengambil instrumen berdasarkan ID.

        Args:
            instrument_id: ID unik instrumen.

        Returns:
            Instance Instrument jika ditemukan, None jika tidak.
        """
        result = await self.db.execute(select(Instrument).where(Instrument.id == instrument_id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Instrument]:
        """Mengambil semua instrumen dengan pagination.

        Args:
            skip: Jumlah record yang dilewati.
            limit: Jumlah maksimal record yang dikembalikan.

        Returns:
            Daftar Instrument.
        """
        result = await self.db.execute(
            select(Instrument).order_by(Instrument.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_user_assignments(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> list[Instrument]:
        """Mengambil instrumen yang ditugaskan ke expert tertentu.

        Args:
            user_id: ID expert.
            skip: Jumlah record yang dilewati.
            limit: Jumlah maksimal record yang dikembalikan.

        Returns:
            Daftar Instrument yang ditugaskan ke expert.
        """
        from app.models.expert_assignment import ExpertAssignment

        result = await self.db.execute(
            select(Instrument)
            .join(ExpertAssignment, ExpertAssignment.instrument_id == Instrument.id)
            .where(ExpertAssignment.user_id == user_id)
            .order_by(Instrument.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, instrument: Instrument) -> Instrument:
        """Menyimpan instrumen baru ke database.

        Args:
            instrument: Instance Instrument yang akan disimpan.

        Returns:
            Instance Instrument yang sudah disimpan.
        """
        self.db.add(instrument)
        await self.db.flush()
        await self.db.refresh(instrument)
        return instrument

    async def update(self, instrument: Instrument) -> Instrument:
        """Memperbarui data instrumen di database.

        Args:
            instrument: Instance Instrument dengan data yang sudah diubah.

        Returns:
            Instance Instrument yang sudah diperbarui.
        """
        await self.db.flush()
        await self.db.refresh(instrument)
        return instrument

    async def delete(self, instrument: Instrument) -> None:
        """Menghapus instrumen dari database.

        Args:
            instrument: Instance Instrument yang akan dihapus.
        """
        await self.db.delete(instrument)
        await self.db.flush()
