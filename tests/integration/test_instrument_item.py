"""Integration test untuk InstrumentService dan ItemService."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.instrument import InstrumentCreate, InstrumentUpdate
from app.schemas.item import ItemBulkCreate, ItemCreate, ItemUpdate
from app.services.instrument_service import InstrumentService
from app.services.item_service import ItemService


async def _create_admin(db: AsyncSession, suffix: str = "a1") -> User:
    """Helper membuat admin user di DB.

    Args:
        db: AsyncSession database.
        suffix: Suffix untuk ID unik.

    Returns:
        User admin yang sudah disimpan.
    """
    repo = UserRepository(db)
    user = User(
        id=f"admin-{suffix}",
        email=f"admin{suffix}@example.com",
        full_name=f"Admin {suffix}",
        role="admin",
        is_active=True,
    )
    return await repo.create(user)


class TestInstrumentService:
    """Kumpulan test untuk InstrumentService."""

    async def test_create_dan_get_by_id(self, db: AsyncSession) -> None:
        """Harus bisa membuat dan mengambil instrumen berdasarkan ID."""
        admin = await _create_admin(db, "ins1")
        service = InstrumentService(db)
        data = InstrumentCreate(name="Instrumen Test", description="Deskripsi", version="1.0")
        instrument = await service.create(data, created_by=admin.id)
        assert instrument.name == "Instrumen Test"
        found = await service.get_by_id(instrument.id)
        assert found.id == instrument.id

    async def test_get_by_id_tidak_ada_raise_404(self, db: AsyncSession) -> None:
        """get_by_id harus raise 404 jika instrumen tidak ditemukan."""
        service = InstrumentService(db)
        with pytest.raises(HTTPException) as exc_info:
            await service.get_by_id("nonexistent")
        assert exc_info.value.status_code == 404

    async def test_get_all_admin(self, db: AsyncSession) -> None:
        """Admin harus dapat melihat semua instrumen."""
        admin = await _create_admin(db, "ins2")
        service = InstrumentService(db)
        await service.create(InstrumentCreate(name="Ins A"), created_by=admin.id)
        await service.create(InstrumentCreate(name="Ins B"), created_by=admin.id)
        instruments = await service.get_all(user_id=admin.id, role="admin")
        names = [i.name for i in instruments]
        assert "Ins A" in names
        assert "Ins B" in names

    async def test_update_instrumen(self, db: AsyncSession) -> None:
        """Harus bisa memperbarui instrumen."""
        admin = await _create_admin(db, "ins3")
        service = InstrumentService(db)
        instrument = await service.create(InstrumentCreate(name="Lama"), created_by=admin.id)
        updated = await service.update(instrument.id, InstrumentUpdate(name="Baru"))
        assert updated.name == "Baru"

    async def test_delete_instrumen(self, db: AsyncSession) -> None:
        """Harus bisa menghapus instrumen."""
        admin = await _create_admin(db, "ins4")
        service = InstrumentService(db)
        instrument = await service.create(InstrumentCreate(name="Hapus Ini"), created_by=admin.id)
        await service.delete(instrument.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.get_by_id(instrument.id)
        assert exc_info.value.status_code == 404


class TestItemService:
    """Kumpulan test untuk ItemService."""

    async def test_create_dan_get(self, db: AsyncSession) -> None:
        """Harus bisa menambahkan item ke instrumen."""
        admin = await _create_admin(db, "item1")
        inst_service = InstrumentService(db)
        instrument = await inst_service.create(
            InstrumentCreate(name="Instrumen Item"), created_by=admin.id
        )
        item_service = ItemService(db)
        item = await item_service.create(
            instrument.id, ItemCreate(sequence_number=1, content="Item konten 1")
        )
        assert item.content == "Item konten 1"
        items = await item_service.get_by_instrument(instrument.id)
        assert len(items) == 1

    async def test_bulk_create(self, db: AsyncSession) -> None:
        """Harus bisa membuat beberapa item sekaligus."""
        admin = await _create_admin(db, "item2")
        inst_service = InstrumentService(db)
        instrument = await inst_service.create(
            InstrumentCreate(name="Instrumen Bulk"), created_by=admin.id
        )
        item_service = ItemService(db)
        bulk_data = ItemBulkCreate(items=[
            ItemCreate(sequence_number=1, content="Item 1"),
            ItemCreate(sequence_number=2, content="Item 2"),
            ItemCreate(sequence_number=3, content="Item 3"),
        ])
        items = await item_service.bulk_create(instrument.id, bulk_data)
        assert len(items) == 3

    async def test_update_item(self, db: AsyncSession) -> None:
        """Harus bisa memperbarui konten item."""
        admin = await _create_admin(db, "item3")
        inst_service = InstrumentService(db)
        instrument = await inst_service.create(
            InstrumentCreate(name="Instrumen Update Item"), created_by=admin.id
        )
        item_service = ItemService(db)
        item = await item_service.create(
            instrument.id, ItemCreate(sequence_number=1, content="Lama")
        )
        updated = await item_service.update(item.id, instrument.id, ItemUpdate(content="Baru"))
        assert updated.content == "Baru"

    async def test_delete_item(self, db: AsyncSession) -> None:
        """Harus bisa menghapus item."""
        admin = await _create_admin(db, "item4")
        inst_service = InstrumentService(db)
        instrument = await inst_service.create(
            InstrumentCreate(name="Instrumen Hapus Item"), created_by=admin.id
        )
        item_service = ItemService(db)
        item = await item_service.create(
            instrument.id, ItemCreate(sequence_number=1, content="Hapus")
        )
        await item_service.delete(item.id, instrument.id)
        items = await item_service.get_by_instrument(instrument.id)
        assert len(items) == 0
