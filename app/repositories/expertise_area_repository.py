"""Repository untuk operasi database entitas ExpertiseArea."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expertise_area import ExpertiseArea


class ExpertiseAreaRepository:
    """Repository untuk operasi CRUD pada tabel expertise_areas.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi ExpertiseAreaRepository.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db

    async def get_by_id(self, expertise_area_id: str) -> ExpertiseArea | None:
        """Mengambil bidang keahlian berdasarkan ID.

        Args:
            expertise_area_id: ID unik bidang keahlian.

        Returns:
            Instance ExpertiseArea jika ditemukan, None jika tidak.
        """
        result = await self.db.execute(
            select(ExpertiseArea).where(ExpertiseArea.id == expertise_area_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, ids: list[str]) -> list[ExpertiseArea]:
        """Mengambil banyak bidang keahlian sekaligus berdasarkan daftar ID.

        Args:
            ids: Daftar ID bidang keahlian.

        Returns:
            Daftar ExpertiseArea yang cocok (tidak menjamin urutan/keberadaan semua ID).
        """
        if not ids:
            return []
        result = await self.db.execute(select(ExpertiseArea).where(ExpertiseArea.id.in_(ids)))
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> ExpertiseArea | None:
        """Mengambil bidang keahlian berdasarkan nama.

        Args:
            name: Nama bidang keahlian.

        Returns:
            Instance ExpertiseArea jika ditemukan, None jika tidak.
        """
        result = await self.db.execute(select(ExpertiseArea).where(ExpertiseArea.name == name))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ExpertiseArea]:
        """Mengambil semua bidang keahlian dengan pagination, terurut nama.

        Args:
            skip: Jumlah record yang dilewati.
            limit: Jumlah maksimal record yang dikembalikan.

        Returns:
            Daftar ExpertiseArea.
        """
        result = await self.db.execute(
            select(ExpertiseArea).order_by(ExpertiseArea.name).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, expertise_area: ExpertiseArea) -> ExpertiseArea:
        """Menyimpan bidang keahlian baru ke database.

        Args:
            expertise_area: Instance ExpertiseArea yang akan disimpan.

        Returns:
            Instance ExpertiseArea yang sudah disimpan.
        """
        self.db.add(expertise_area)
        await self.db.flush()
        await self.db.refresh(expertise_area)
        return expertise_area

    async def update(self, expertise_area: ExpertiseArea) -> ExpertiseArea:
        """Memperbarui data bidang keahlian di database.

        Args:
            expertise_area: Instance ExpertiseArea dengan data yang sudah diubah.

        Returns:
            Instance ExpertiseArea yang sudah diperbarui.
        """
        await self.db.flush()
        await self.db.refresh(expertise_area)
        return expertise_area

    async def delete(self, expertise_area: ExpertiseArea) -> None:
        """Menghapus bidang keahlian dari database.

        Args:
            expertise_area: Instance ExpertiseArea yang akan dihapus.
        """
        await self.db.delete(expertise_area)
        await self.db.flush()
