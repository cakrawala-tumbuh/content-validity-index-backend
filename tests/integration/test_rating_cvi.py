"""Integration test untuk ExpertAssignmentService, RatingService, dan CVIService."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.expert_assignment import AssignmentCreate
from app.schemas.instrument import InstrumentCreate
from app.schemas.item import ItemCreate
from app.schemas.rating import RatingBulkCreate, RatingItem
from app.services.cvi_service import CVIService
from app.services.expert_assignment_service import ExpertAssignmentService
from app.services.instrument_service import InstrumentService
from app.services.item_service import ItemService


async def _setup_instrument_with_items(
    db: AsyncSession, suffix: str = "x"
) -> tuple[User, User, str]:
    """Helper menyiapkan instrumen dengan 3 item dan 2 user (admin + expert).

    Args:
        db: AsyncSession database.
        suffix: Suffix untuk ID unik.

    Returns:
        Tuple (admin, expert, instrument_id).
    """
    repo = UserRepository(db)
    admin = await repo.create(User(
        id=f"adm-{suffix}", email=f"adm{suffix}@test.com",
        full_name="Admin", role="admin", is_active=True,
    ))
    expert = await repo.create(User(
        id=f"exp-{suffix}", email=f"exp{suffix}@test.com",
        full_name="Expert", role="expert", is_active=True,
    ))

    inst_service = InstrumentService(db)
    instrument = await inst_service.create(
        InstrumentCreate(name=f"Instrumen {suffix}"), created_by=admin.id
    )

    item_service = ItemService(db)
    for i in range(1, 4):
        await item_service.create(
            instrument.id, ItemCreate(sequence_number=i, content=f"Item {i}")
        )

    return admin, expert, instrument.id


class TestExpertAssignmentService:
    """Kumpulan test untuk ExpertAssignmentService."""

    async def test_create_assignment(self, db: AsyncSession) -> None:
        """Harus bisa menugaskan expert ke instrumen."""
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "ea1")
        service = ExpertAssignmentService(db)
        assignment = await service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )
        assert assignment.user_id == expert.id
        assert assignment.instrument_id == instrument_id

    async def test_create_assignment_duplikat_raise_409(self, db: AsyncSession) -> None:
        """Harus raise 400 jika expert sudah di-assign ke instrumen yang sama."""
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "ea2")
        service = ExpertAssignmentService(db)
        await service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.create(
                instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
            )
        assert exc_info.value.status_code == 409

    async def test_get_by_instrument(self, db: AsyncSession) -> None:
        """Harus mengembalikan assignment berdasarkan instrumen."""
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "ea3")
        service = ExpertAssignmentService(db)
        await service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )
        assignments = await service.get_by_instrument(instrument_id)
        assert len(assignments) == 1

    async def test_delete_assignment(self, db: AsyncSession) -> None:
        """Harus bisa menghapus assignment."""
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "ea4")
        service = ExpertAssignmentService(db)
        assignment = await service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )
        await service.delete(assignment.id)
        assignments = await service.get_by_instrument(instrument_id)
        assert len(assignments) == 0


class TestRatingService:
    """Kumpulan test untuk RatingService."""

    async def test_bulk_submit_dan_get(self, db: AsyncSession) -> None:
        """Harus bisa menyimpan dan mengambil penilaian bulk."""
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "rs1")
        assign_service = ExpertAssignmentService(db)
        assignment = await assign_service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )

        item_service = ItemService(db)
        items = await item_service.get_by_instrument(instrument_id)

        from app.services.rating_service import RatingService
        rating_service = RatingService(db)
        bulk_data = RatingBulkCreate(ratings=[
            RatingItem(item_id=item.id, relevance_score=4) for item in items
        ])
        ratings = await rating_service.bulk_submit(assignment.id, expert.id, bulk_data)
        assert len(ratings) == 3

    async def test_bulk_submit_update_status_assignment(self, db: AsyncSession) -> None:
        """Status assignment harus menjadi 'completed' setelah semua item dinilai."""
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "rs2")
        assign_service = ExpertAssignmentService(db)
        assignment = await assign_service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )

        item_service = ItemService(db)
        items = await item_service.get_by_instrument(instrument_id)

        from app.services.rating_service import RatingService
        rating_service = RatingService(db)
        bulk_data = RatingBulkCreate(ratings=[
            RatingItem(item_id=item.id, relevance_score=3) for item in items
        ])
        await rating_service.bulk_submit(assignment.id, expert.id, bulk_data)

        # Verifikasi status assignment
        updated_assignment = await assign_service.get_by_id(assignment.id)
        assert updated_assignment.status == "completed"


class TestCVIService:
    """Kumpulan test untuk CVIService dengan DB."""

    async def test_calculate_cvi_lengkap(self, db: AsyncSession) -> None:
        """Harus bisa menghitung CVI setelah semua expert memberikan penilaian."""
        admin, expert1, instrument_id = await _setup_instrument_with_items(db, "cvi1")
        repo = UserRepository(db)
        expert2 = await repo.create(User(
            id="exp2-cvi1", email="exp2cvi1@test.com",
            full_name="Expert 2", role="expert", is_active=True,
        ))

        assign_service = ExpertAssignmentService(db)
        asgn1 = await assign_service.create(
            instrument_id, AssignmentCreate(user_id=expert1.id), assigned_by=admin.id
        )
        asgn2 = await assign_service.create(
            instrument_id, AssignmentCreate(user_id=expert2.id), assigned_by=admin.id
        )

        item_service = ItemService(db)
        items = await item_service.get_by_instrument(instrument_id)

        from app.services.rating_service import RatingService
        rating_service = RatingService(db)

        # Expert 1: semua relevan (skor 4)
        await rating_service.bulk_submit(asgn1.id, expert1.id, RatingBulkCreate(ratings=[
            RatingItem(item_id=item.id, relevance_score=4) for item in items
        ]))
        # Expert 2: semua relevan (skor 3)
        await rating_service.bulk_submit(asgn2.id, expert2.id, RatingBulkCreate(ratings=[
            RatingItem(item_id=item.id, relevance_score=3) for item in items
        ]))

        cvi_service = CVIService(db)
        result = await cvi_service.calculate(instrument_id)

        assert result.n_experts == 2
        assert result.n_items == 3
        assert result.s_cvi_ave == 1.0
        assert result.s_cvi_ua == 1.0
        for item_result in result.items:
            assert item_result.i_cvi == 1.0

    async def test_calculate_cvi_tanpa_rating_raise_400(self, db: AsyncSession) -> None:
        """calculate harus raise 400 jika belum ada penilaian."""
        admin, _, instrument_id = await _setup_instrument_with_items(db, "cvi2")
        cvi_service = CVIService(db)
        with pytest.raises(HTTPException) as exc_info:
            await cvi_service.calculate(instrument_id)
        assert exc_info.value.status_code == 400

    async def test_calculate_cvi_instrumen_tidak_ada(self, db: AsyncSession) -> None:
        """calculate harus raise 404 jika instrumen tidak ada."""
        cvi_service = CVIService(db)
        with pytest.raises(HTTPException) as exc_info:
            await cvi_service.calculate("nonexistent")
        assert exc_info.value.status_code == 404
