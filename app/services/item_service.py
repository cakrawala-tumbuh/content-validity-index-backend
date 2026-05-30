"""Service untuk pengelolaan Item."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.repositories.item_repository import ItemRepository
from app.schemas.item import ItemBulkCreate, ItemCreate, ItemUpdate


class ItemService:
    """Service yang menangani business logic untuk entitas Item.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi ItemService.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db
        self.repo = ItemRepository(db)

    async def get_by_instrument(self, instrument_id: str) -> list[Item]:
        """Mengambil semua item dalam sebuah instrumen.

        Args:
            instrument_id: ID instrumen.

        Returns:
            Daftar Item diurutkan berdasarkan sequence_number.
        """
        return await self.repo.get_by_instrument(instrument_id)

    async def get_by_id(self, item_id: str, instrument_id: str) -> Item:
        """Mengambil item berdasarkan ID dan memvalidasi kepemilikannya.

        Args:
            item_id: ID unik item.
            instrument_id: ID instrumen pemilik item.

        Returns:
            Instance Item.

        Raises:
            HTTPException: Jika item tidak ditemukan atau tidak milik instrumen tersebut (404).
        """
        item = await self.repo.get_by_id(item_id)
        if not item or item.instrument_id != instrument_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item dengan ID '{item_id}' tidak ditemukan.",
            )
        return item

    async def create(self, instrument_id: str, data: ItemCreate) -> Item:
        """Membuat item baru dalam sebuah instrumen.

        Args:
            instrument_id: ID instrumen tempat item dibuat.
            data: Data item baru.

        Returns:
            Instance Item yang sudah dibuat.
        """
        item = Item(
            id=str(uuid.uuid4()),
            instrument_id=instrument_id,
            sequence_number=data.sequence_number,
            content=data.content,
            dimension_id=data.dimension_id,
        )
        return await self.repo.create(item)

    async def bulk_create(self, instrument_id: str, data: ItemBulkCreate) -> list[Item]:
        """Membuat banyak item sekaligus dalam sebuah instrumen.

        Args:
            instrument_id: ID instrumen tempat item dibuat.
            data: Data berisi daftar item yang akan dibuat.

        Returns:
            Daftar Instance Item yang sudah dibuat.
        """
        items = [
            Item(
                id=str(uuid.uuid4()),
                instrument_id=instrument_id,
                sequence_number=item_data.sequence_number,
                content=item_data.content,
                dimension_id=item_data.dimension_id,
            )
            for item_data in data.items
        ]
        return await self.repo.bulk_create(items)

    async def update(self, item_id: str, instrument_id: str, data: ItemUpdate) -> Item:
        """Memperbarui data item.

        Args:
            item_id: ID item yang akan diperbarui.
            instrument_id: ID instrumen pemilik item.
            data: Data pembaruan item.

        Returns:
            Instance Item yang sudah diperbarui.

        Raises:
            HTTPException: Jika item tidak ditemukan (404).
        """
        item = await self.get_by_id(item_id, instrument_id)
        if data.sequence_number is not None:
            item.sequence_number = data.sequence_number
        if data.content is not None:
            item.content = data.content
        if data.dimension_id is not None:
            item.dimension_id = data.dimension_id
        return await self.repo.update(item)

    async def delete(self, item_id: str, instrument_id: str) -> None:
        """Menghapus item dari instrumen.

        Args:
            item_id: ID item yang akan dihapus.
            instrument_id: ID instrumen pemilik item.

        Raises:
            HTTPException: Jika item tidak ditemukan (404).
        """
        item = await self.get_by_id(item_id, instrument_id)
        await self.repo.delete(item)
