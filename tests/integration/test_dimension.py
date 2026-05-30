"""Integration test untuk DimensionService dan Item dengan dimension_id."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.dimension import DimensionBulkCreate, DimensionCreate, DimensionUpdate
from app.schemas.instrument import InstrumentCreate
from app.schemas.item import ItemCreate, ItemUpdate
from app.services.dimension_service import DimensionService
from app.services.instrument_service import InstrumentService
from app.services.item_service import ItemService


@pytest.fixture
async def _setup_instrument(db: AsyncSession) -> tuple[User, str]:
    """Helper menyiapkan admin user dan instrumen.

    Args:
        db: AsyncSession database.

    Returns:
        Tuple (admin, instrument_id).
    """
    repo = UserRepository(db)
    admin = await repo.create(
        User(
            id="adm-dimtest",
            email="adm-dimtest@test.com",
            full_name="Admin",
            role="admin",
            is_active=True,
        )
    )
    inst_service = InstrumentService(db)
    instrument = await inst_service.create(
        InstrumentCreate(name="Instrumen Dimensi Test"), created_by=admin.id
    )
    return admin, instrument.id


class TestDimensionServiceIntegration:
    """Kumpulan integration test untuk DimensionService."""

    async def test_create_dimension(self, db: AsyncSession) -> None:
        """Harus bisa membuat dimensi baru di instrumen."""
        _, instrument_id = await _setup_instrument(db)
        service = DimensionService(db)
        dim = await service.create(
            instrument_id,
            DimensionCreate(name="Stability of Change", description="Dimensi stabilitas"),
        )
        assert dim.name == "Stability of Change"
        assert dim.description == "Dimensi stabilitas"
        assert dim.instrument_id == instrument_id

    async def test_bulk_create_dimensions(self, db: AsyncSession) -> None:
        """Harus bisa membuat banyak dimensi sekaligus."""
        _, instrument_id = await _setup_instrument(db)
        service = DimensionService(db)
        dims = await service.bulk_create(
            instrument_id,
            DimensionBulkCreate(
                dimensions=[
                    DimensionCreate(name="Stability of Change"),
                    DimensionCreate(name="Technology Maturity"),
                    DimensionCreate(name="Role Clarity"),
                ]
            ),
        )
        assert len(dims) == 3
        names = {d.name for d in dims}
        assert "Stability of Change" in names
        assert "Technology Maturity" in names
        assert "Role Clarity" in names

    async def test_get_by_instrument(self, db: AsyncSession) -> None:
        """Harus mengembalikan dimensi yang dimiliki instrumen."""
        _, instrument_id = await _setup_instrument(db)
        service = DimensionService(db)
        await service.bulk_create(
            instrument_id,
            DimensionBulkCreate(
                dimensions=[
                    DimensionCreate(name="Admin Support"),
                    DimensionCreate(name="Role Clarity"),
                ]
            ),
        )
        dims = await service.get_by_instrument(instrument_id)
        assert len(dims) == 2

    async def test_update_dimension(self, db: AsyncSession) -> None:
        """Harus bisa memperbarui nama dimensi."""
        _, instrument_id = await _setup_instrument(db)
        service = DimensionService(db)
        dim = await service.create(instrument_id, DimensionCreate(name="Old Name"))
        updated = await service.update(dim.id, instrument_id, DimensionUpdate(name="New Name"))
        assert updated.name == "New Name"

    async def test_delete_dimension(self, db: AsyncSession) -> None:
        """Harus bisa menghapus dimensi."""
        _, instrument_id = await _setup_instrument(db)
        service = DimensionService(db)
        dim = await service.create(instrument_id, DimensionCreate(name="To Delete"))
        await service.delete(dim.id, instrument_id)
        dims = await service.get_by_instrument(instrument_id)
        assert len(dims) == 0


class TestItemWithDimensionIntegration:
    """Kumpulan integration test item dengan dimension_id."""

    async def test_create_item_with_dimension_id(self, db: AsyncSession) -> None:
        """Harus bisa membuat item dengan dimension_id."""
        _, instrument_id = await _setup_instrument(db)
        dim_service = DimensionService(db)
        dim = await dim_service.create(
            instrument_id, DimensionCreate(name="Role Clarity")
        )

        item_service = ItemService(db)
        item = await item_service.create(
            instrument_id,
            ItemCreate(sequence_number=1, content="Item dengan dimensi", dimension_id=dim.id),
        )
        assert item.dimension_id == dim.id
        assert item.content == "Item dengan dimensi"

    async def test_create_item_tanpa_dimension(self, db: AsyncSession) -> None:
        """Harus bisa membuat item tanpa dimension_id."""
        _, instrument_id = await _setup_instrument(db)
        item_service = ItemService(db)
        item = await item_service.create(
            instrument_id,
            ItemCreate(sequence_number=1, content="Item tanpa dimensi"),
        )
        assert item.dimension_id is None
        assert item.content == "Item tanpa dimensi"

    async def test_update_item_dimension_id(self, db: AsyncSession) -> None:
        """Harus bisa mengubah dimension_id item."""
        _, instrument_id = await _setup_instrument(db)
        dim_service = DimensionService(db)
        dim1 = await dim_service.create(instrument_id, DimensionCreate(name="Dim A"))
        dim2 = await dim_service.create(instrument_id, DimensionCreate(name="Dim B"))

        item_service = ItemService(db)
        item = await item_service.create(
            instrument_id,
            ItemCreate(sequence_number=1, content="Item", dimension_id=dim1.id),
        )
        assert item.dimension_id == dim1.id

        updated = await item_service.update(
            item.id, instrument_id, ItemUpdate(dimension_id=dim2.id)
        )
        assert updated.dimension_id == dim2.id

    async def test_clear_dimension_from_item(self, db: AsyncSession) -> None:
        """Harus bisa menghapus dimensi dari item (set ke None/null)."""
        _, instrument_id = await _setup_instrument(db)
        dim_service = DimensionService(db)
        dim = await dim_service.create(instrument_id, DimensionCreate(name="Dim"))

        item_service = ItemService(db)
        item = await item_service.create(
            instrument_id,
            ItemCreate(sequence_number=1, content="Item berdimensi", dimension_id=dim.id),
        )
        # None artinya kita set dimension_id jadi null
        updated = await item_service.update(
            item.id, instrument_id, ItemUpdate(dimension_id=None)
        )
        assert updated.dimension_id is None

    async def test_dimension_name_preloaded(self, db: AsyncSession) -> None:
        """Harus bisa mendapatkan dimension_name melalui properti item."""
        _, instrument_id = await _setup_instrument(db)
        dim_service = DimensionService(db)
        dim = await dim_service.create(
            instrument_id, DimensionCreate(name="Stability of Change")
        )

        item_service = ItemService(db)
        item = await item_service.create(
            instrument_id,
            ItemCreate(sequence_number=1, content="Item", dimension_id=dim.id),
        )
        # Fetch ulang untuk memastikan relasi eager-loaded
        item_fresh = await item_service.get_by_id(item.id, instrument_id)
        assert item_fresh.dimension_name == "Stability of Change"