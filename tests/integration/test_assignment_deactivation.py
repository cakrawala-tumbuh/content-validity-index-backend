"""Integration test untuk penonaktifan (deactivate/activate) penilaian expert."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user, require_admin
from app.main import app
from app.models.user import User
from app.repositories.rating_repository import RatingRepository
from app.repositories.user_repository import UserRepository
from app.schemas.expert_assignment import AssignmentCreate
from app.schemas.instrument import InstrumentCreate
from app.schemas.item import ItemCreate
from app.schemas.rating import RatingBulkCreate, RatingItem
from app.services.expert_assignment_service import ExpertAssignmentService
from app.services.instrument_service import InstrumentService
from app.services.item_service import ItemService
from app.services.rating_service import RatingService


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
    admin = await repo.create(
        User(
            id=f"adm-{suffix}",
            email=f"adm{suffix}@test.com",
            full_name="Admin",
            role="admin",
            is_active=True,
        )
    )
    expert = await repo.create(
        User(
            id=f"exp-{suffix}",
            email=f"exp{suffix}@test.com",
            full_name="Expert",
            role="expert",
            is_active=True,
        )
    )

    inst_service = InstrumentService(db)
    instrument = await inst_service.create(
        InstrumentCreate(name=f"Instrumen {suffix}"), created_by=admin.id
    )

    item_service = ItemService(db)
    for i in range(1, 4):
        await item_service.create(instrument.id, ItemCreate(sequence_number=i, content=f"Item {i}"))

    return admin, expert, instrument.id


class TestRatingRepositoryExcludesInactiveAssignment:
    """Kumpulan test yang membuktikan RatingRepository.get_by_instrument mengeksklusi
    rating dari assignment yang is_active=False."""

    async def test_get_by_instrument_tidak_mengembalikan_rating_assignment_nonaktif(
        self, db: AsyncSession
    ) -> None:
        """Rating dari assignment is_active=False tidak boleh muncul di get_by_instrument."""
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "deact1")

        assign_service = ExpertAssignmentService(db)
        assignment = await assign_service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )

        item_service = ItemService(db)
        items = await item_service.get_by_instrument(instrument_id)

        rating_service = RatingService(db)
        await rating_service.bulk_submit(
            assignment.id,
            expert.id,
            RatingBulkCreate(
                ratings=[RatingItem(item_id=item.id, relevance_score=4) for item in items]
            ),
        )

        rating_repo = RatingRepository(db)
        ratings_before = await rating_repo.get_by_instrument(instrument_id)
        assert len(ratings_before) == 3

        await assign_service.set_active(assignment.id, is_active=False)

        ratings_after = await rating_repo.get_by_instrument(instrument_id)
        assert ratings_after == []

    async def test_get_by_instrument_mengembalikan_rating_setelah_diaktifkan_kembali(
        self, db: AsyncSession
    ) -> None:
        """Rating harus kembali muncul di get_by_instrument setelah assignment diaktifkan."""
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "deact2")

        assign_service = ExpertAssignmentService(db)
        assignment = await assign_service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )

        item_service = ItemService(db)
        items = await item_service.get_by_instrument(instrument_id)

        rating_service = RatingService(db)
        await rating_service.bulk_submit(
            assignment.id,
            expert.id,
            RatingBulkCreate(
                ratings=[RatingItem(item_id=item.id, relevance_score=4) for item in items]
            ),
        )

        rating_repo = RatingRepository(db)
        await assign_service.set_active(assignment.id, is_active=False)
        assert await rating_repo.get_by_instrument(instrument_id) == []

        await assign_service.set_active(assignment.id, is_active=True)
        ratings_after = await rating_repo.get_by_instrument(instrument_id)
        assert len(ratings_after) == 3


class TestDeactivateActivateAssignmentEndpoint:
    """Kumpulan test untuk endpoint deactivate/activate assignment."""

    async def test_deactivate_assignment_mengubah_is_active_false(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """POST .../deactivate harus mengembalikan is_active=False di response dan DB."""
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "ep1")
        assign_service = ExpertAssignmentService(db)
        assignment = await assign_service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )

        app.dependency_overrides[require_admin] = lambda: admin
        try:
            resp = await client.post(
                f"/api/v1/instruments/{instrument_id}/assignments/{assignment.id}/deactivate"
            )
        finally:
            app.dependency_overrides.pop(require_admin, None)

        assert resp.status_code == 200
        body = resp.json()
        assert body["is_active"] is False

        updated = await assign_service.get_by_id(assignment.id)
        assert updated.is_active is False

    async def test_activate_assignment_mengembalikan_is_active_true(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """POST .../activate harus mengembalikan is_active=True setelah dinonaktifkan."""
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "ep2")
        assign_service = ExpertAssignmentService(db)
        assignment = await assign_service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )
        await assign_service.set_active(assignment.id, is_active=False)

        app.dependency_overrides[require_admin] = lambda: admin
        try:
            resp = await client.post(
                f"/api/v1/instruments/{instrument_id}/assignments/{assignment.id}/activate"
            )
        finally:
            app.dependency_overrides.pop(require_admin, None)

        assert resp.status_code == 200
        body = resp.json()
        assert body["is_active"] is True

        updated = await assign_service.get_by_id(assignment.id)
        assert updated.is_active is True

    async def test_deactivate_assignment_non_admin_raise_403(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """POST .../deactivate harus mengembalikan 403 jika user bukan admin."""
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "ep3")
        assign_service = ExpertAssignmentService(db)
        assignment = await assign_service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )

        app.dependency_overrides[get_current_user] = lambda: expert
        try:
            resp = await client.post(
                f"/api/v1/instruments/{instrument_id}/assignments/{assignment.id}/deactivate"
            )
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert resp.status_code == 403

    async def test_deactivate_assignment_tidak_ada_raise_404(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """POST .../deactivate harus mengembalikan 404 jika assignment tidak ditemukan."""
        admin, _, instrument_id = await _setup_instrument_with_items(db, "ep4")

        app.dependency_overrides[require_admin] = lambda: admin
        try:
            resp = await client.post(
                f"/api/v1/instruments/{instrument_id}/assignments/nonexistent/deactivate"
            )
        finally:
            app.dependency_overrides.pop(require_admin, None)

        assert resp.status_code == 404
