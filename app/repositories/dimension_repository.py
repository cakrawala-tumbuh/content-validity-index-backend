"""Repository untuk operasi database entitas Dimension."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dimension import Dimension


class DimensionRepository:
    """Repository untuk operasi CRUD pada tabel dimensions.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi DimensionRepository.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db

    async def get_by_id(self, dimension_id: str) -> Dimension | None:
        """Mengambil dimensi berdasarkan ID.

        Args:
            dimension_id: ID unik dimensi.

        Returns:
            Instance Dimension jika ditemukan, None jika tidak.
        """
        result = await self.db.execute(
            select(Dimension).where(Dimension.id == dimension_id)
        )
        return result.scalar_one_or_none()

    async def get_by_instrument(self, instrument_id: str) -> list[Dimension]:
        """Mengambil semua dimensi dalam sebuah instrumen.

        Args:
            instrument_id: ID instrumen.

        Returns:
            Daftar Dimension yang diurutkan berdasarkan nama.
        """
        result = await self.db.execute(
            select(Dimension)
            .where(Dimension.instrument_id == instrument_id)
            .order_by(Dimension.name)
        )
        return list(result.scalars().all())

    async def create(self, dimension: Dimension) -> Dimension:
        """Menyimpan dimensi baru ke database.

        Args:
            dimension: Instance Dimension yang akan disimpan.

        Returns:
            Instance Dimension yang sudah disimpan.
        """
        self.db.add(dimension)
        await self.db.flush()
        await self.db.refresh(dimension)
        return dimension

    async def bulk_create(self, dimensions: list[Dimension]) -> list[Dimension]:
        """Menyimpan banyak dimensi sekaligus ke database.

        Args:
            dimensions: Daftar Instance Dimension yang akan disimpan.

        Returns:
            Daftar Instance Dimension yang sudah disimpan.
        """
        for dimension in dimensions:
            self.db.add(dimension)
        await self.db.flush()
        for dimension in dimensions:
            await self.db.refresh(dimension)
        return dimensions

    async def update(self, dimension: Dimension) -> Dimension:
        """Memperbarui data dimensi di database.

        Args:
            dimension: Instance Dimension dengan data yang sudah diubah.

        Returns:
            Instance Dimension yang sudah diperbarui.
        """
        await self.db.flush()
        await self.db.refresh(dimension)
        return dimension

    async def delete(self, dimension: Dimension) -> None:
        """Menghapus dimensi dari database.

        Args:
            dimension: Instance Dimension yang akan dihapus.
        """
        await self.db.delete(dimension)
        await self.db.flush()