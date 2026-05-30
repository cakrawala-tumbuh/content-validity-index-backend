"""Repository untuk operasi database entitas Item."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item


class ItemRepository:
    """Repository untuk operasi CRUD pada tabel items.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi ItemRepository.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db

    async def get_by_id(self, item_id: str) -> Item | None:
        """Mengambil item berdasarkan ID.

        Args:
            item_id: ID unik item.

        Returns:
            Instance Item jika ditemukan, None jika tidak.
        """
        result = await self.db.execute(select(Item).where(Item.id == item_id))
        return result.scalar_one_or_none()

    async def get_by_instrument(self, instrument_id: str) -> list[Item]:
        """Mengambil semua item dalam sebuah instrumen, diurutkan berdasarkan nomor urut.

        Args:
            instrument_id: ID instrumen.

        Returns:
            Daftar Item yang diurutkan berdasarkan sequence_number.
        """
        result = await self.db.execute(
            select(Item).where(Item.instrument_id == instrument_id).order_by(Item.sequence_number)
        )
        return list(result.scalars().all())

    async def create(self, item: Item) -> Item:
        """Menyimpan item baru ke database.

        Args:
            item: Instance Item yang akan disimpan.

        Returns:
            Instance Item yang sudah disimpan.
        """
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def bulk_create(self, items: list[Item]) -> list[Item]:
        """Menyimpan banyak item sekaligus ke database.

        Args:
            items: Daftar Instance Item yang akan disimpan.

        Returns:
            Daftar Instance Item yang sudah disimpan.
        """
        for item in items:
            self.db.add(item)
        await self.db.flush()
        for item in items:
            await self.db.refresh(item)
        return items

    async def update(self, item: Item) -> Item:
        """Memperbarui data item di database.

        Args:
            item: Instance Item dengan data yang sudah diubah.

        Returns:
            Instance Item yang sudah diperbarui.
        """
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, item: Item) -> None:
        """Menghapus item dari database.

        Args:
            item: Instance Item yang akan dihapus.
        """
        await self.db.delete(item)
        await self.db.flush()
