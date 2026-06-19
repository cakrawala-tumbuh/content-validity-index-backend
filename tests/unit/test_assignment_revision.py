"""Unit test untuk mekanisme pengarsipan dan revisi ExpertAssignment."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestArchiveAndRevise:
    """Kumpulan test untuk ExpertAssignmentService.archive_and_revise()."""

    def _make_mock_assignment(
        self,
        assignment_id: str = "assign-1",
        user_id: str = "expert-1",
        instrument_id: str = "instr-1",
        status: str = "completed",
        revision_number: int = 1,
        deadline: object = None,
    ) -> MagicMock:
        """Membuat mock ExpertAssignment dengan atribut standar.

        Args:
            assignment_id: ID assignment.
            user_id: ID expert.
            instrument_id: ID instrumen.
            status: Status assignment.
            revision_number: Nomor revisi saat ini.
            deadline: Batas waktu (opsional).

        Returns:
            MagicMock yang merepresentasikan ExpertAssignment.
        """
        mock = MagicMock()
        mock.id = assignment_id
        mock.user_id = user_id
        mock.instrument_id = instrument_id
        mock.status = status
        mock.revision_number = revision_number
        mock.deadline = deadline
        return mock

    def _make_mock_rating(
        self,
        rating_id: str,
        item_id: str,
        relevance_score: int,
        notes: str | None = None,
    ) -> MagicMock:
        """Membuat mock Rating.

        Args:
            rating_id: ID rating.
            item_id: ID item yang dinilai.
            relevance_score: Skor relevansi 1-4.
            notes: Catatan opsional.

        Returns:
            MagicMock yang merepresentasikan Rating.
        """
        mock = MagicMock()
        mock.id = rating_id
        mock.item_id = item_id
        mock.user_id = "expert-1"
        mock.relevance_score = relevance_score
        mock.notes = notes
        return mock

    @pytest.mark.asyncio
    async def test_archive_and_revise_mengarsipkan_assignment_lama(self) -> None:
        """archive_and_revise harus mengubah status assignment lama menjadi 'archived'."""
        mock_db = AsyncMock()
        mock_assignment = self._make_mock_assignment()
        mock_new_assignment = self._make_mock_assignment(
            assignment_id="assign-new", revision_number=2
        )

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment
        mock_repo.update.return_value = mock_assignment
        mock_repo.create.return_value = mock_new_assignment

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = []

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            await service.archive_and_revise("assign-1", "admin-1")

        assert mock_assignment.status == "archived"

    @pytest.mark.asyncio
    async def test_archive_and_revise_membuat_assignment_baru(self) -> None:
        """archive_and_revise harus membuat assignment baru untuk expert/instrumen yang sama."""
        mock_db = AsyncMock()
        mock_assignment = self._make_mock_assignment()
        captured: list = []

        async def capture_create(new_assign: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(new_assign)
            return new_assign

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment
        mock_repo.update.return_value = mock_assignment
        mock_repo.create.side_effect = capture_create

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = []

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            await service.archive_and_revise("assign-1", "admin-1")

        assert len(captured) == 1
        new_assign = captured[0]
        assert new_assign.instrument_id == "instr-1"
        assert new_assign.user_id == "expert-1"
        assert new_assign.assigned_by == "admin-1"

    @pytest.mark.asyncio
    async def test_archive_and_revise_nomor_revisi_bertambah(self) -> None:
        """assignment baru harus memiliki revision_number = lama + 1."""
        mock_db = AsyncMock()
        mock_assignment = self._make_mock_assignment(revision_number=3)
        captured: list = []

        async def capture_create(new_assign: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(new_assign)
            return new_assign

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment
        mock_repo.update.return_value = mock_assignment
        mock_repo.create.side_effect = capture_create

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = []

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            await service.archive_and_revise("assign-1", "admin-1")

        assert captured[0].revision_number == 4

    @pytest.mark.asyncio
    async def test_archive_and_revise_previous_assignment_id_terisi(self) -> None:
        """assignment baru harus memiliki previous_assignment_id = ID assignment lama."""
        mock_db = AsyncMock()
        mock_assignment = self._make_mock_assignment(assignment_id="assign-original")
        captured: list = []

        async def capture_create(new_assign: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(new_assign)
            return new_assign

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment
        mock_repo.update.return_value = mock_assignment
        mock_repo.create.side_effect = capture_create

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = []

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            await service.archive_and_revise("assign-original", "admin-1")

        assert captured[0].previous_assignment_id == "assign-original"

    @pytest.mark.asyncio
    async def test_archive_and_revise_menyalin_semua_rating(self) -> None:
        """archive_and_revise harus menyalin semua rating ke assignment baru."""
        mock_db = AsyncMock()
        mock_assignment = self._make_mock_assignment()
        mock_new_assignment = MagicMock()
        mock_new_assignment.id = "assign-new"

        ratings = [
            self._make_mock_rating("r1", "item-1", 4),
            self._make_mock_rating("r2", "item-2", 2, notes="Perlu revisi"),
            self._make_mock_rating("r3", "item-3", 3),
        ]

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment
        mock_repo.update.return_value = mock_assignment
        mock_repo.create.return_value = mock_new_assignment

        created_ratings: list = []

        async def capture_rating_create(rating: object) -> object:
            """Menangkap argumen yang diteruskan ke rating_repo.create."""
            created_ratings.append(rating)
            return rating

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = ratings
        mock_rating_repo.create.side_effect = capture_rating_create

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            await service.archive_and_revise("assign-1", "admin-1")

        assert len(created_ratings) == 3
        item_ids_created = {r.item_id for r in created_ratings}
        assert item_ids_created == {"item-1", "item-2", "item-3"}

    @pytest.mark.asyncio
    async def test_archive_and_revise_rating_salin_preserves_score_and_notes(self) -> None:
        """Rating yang disalin harus mempertahankan relevance_score dan notes."""
        mock_db = AsyncMock()
        mock_assignment = self._make_mock_assignment()
        mock_new_assignment = MagicMock()
        mock_new_assignment.id = "assign-new"

        original_rating = self._make_mock_rating("r1", "item-1", 2, notes="Tidak relevan")

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment
        mock_repo.update.return_value = mock_assignment
        mock_repo.create.return_value = mock_new_assignment

        created_ratings: list = []

        async def capture_rating_create(rating: object) -> object:
            """Menangkap argumen yang diteruskan ke rating_repo.create."""
            created_ratings.append(rating)
            return rating

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = [original_rating]
        mock_rating_repo.create.side_effect = capture_rating_create

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            await service.archive_and_revise("assign-1", "admin-1")

        copied = created_ratings[0]
        assert copied.relevance_score == 2
        assert copied.notes == "Tidak relevan"
        assert copied.assignment_id == "assign-new"

    @pytest.mark.asyncio
    async def test_archive_and_revise_tanpa_rating_status_pending(self) -> None:
        """assignment baru harus berstatus 'pending' jika tidak ada rating sebelumnya."""
        mock_db = AsyncMock()
        mock_assignment = self._make_mock_assignment()
        captured: list = []

        async def capture_create(new_assign: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(new_assign)
            return new_assign

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment
        mock_repo.update.return_value = mock_assignment
        mock_repo.create.side_effect = capture_create

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = []

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            await service.archive_and_revise("assign-1", "admin-1")

        assert captured[0].status == "pending"

    @pytest.mark.asyncio
    async def test_archive_and_revise_dengan_rating_status_in_progress(self) -> None:
        """assignment baru harus berstatus 'in_progress' jika ada rating sebelumnya."""
        mock_db = AsyncMock()
        mock_assignment = self._make_mock_assignment()
        mock_new_assignment = MagicMock()
        mock_new_assignment.id = "assign-new"
        captured: list = []

        async def capture_create(new_assign: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(new_assign)
            return new_assign

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment
        mock_repo.update.return_value = mock_assignment
        mock_repo.create.side_effect = capture_create

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = [
            self._make_mock_rating("r1", "item-1", 4)
        ]
        mock_rating_repo.create.return_value = MagicMock()

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            await service.archive_and_revise("assign-1", "admin-1")

        assert captured[0].status == "in_progress"

    @pytest.mark.asyncio
    async def test_archive_and_revise_assignment_tidak_ditemukan_raise_404(self) -> None:
        """archive_and_revise harus raise HTTPException 404 jika assignment tidak ada."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=AsyncMock(),
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.archive_and_revise("nonexistent", "admin-1")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_archive_and_revise_sudah_archived_raise_400(self) -> None:
        """archive_and_revise harus raise HTTPException 400 jika sudah berstatus archived."""
        mock_db = AsyncMock()
        mock_assignment = self._make_mock_assignment(status="archived")

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=AsyncMock(),
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.archive_and_revise("assign-archived", "admin-1")

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_archive_and_revise_mengembalikan_tuple_dua_assignment(self) -> None:
        """archive_and_revise harus mengembalikan (archived_assignment, new_assignment)."""
        mock_db = AsyncMock()
        mock_assignment = self._make_mock_assignment()
        mock_new_assignment = self._make_mock_assignment(
            assignment_id="assign-new", revision_number=2
        )

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment
        mock_repo.update.return_value = mock_assignment
        mock_repo.create.return_value = mock_new_assignment

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = []

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            archived, new_assign = await service.archive_and_revise("assign-1", "admin-1")

        assert archived is mock_assignment
        assert new_assign is mock_new_assignment

    @pytest.mark.asyncio
    async def test_archive_and_revise_rating_baru_punya_id_unik(self) -> None:
        """Setiap rating yang disalin harus mendapat UUID baru, berbeda dari ID lama."""
        mock_db = AsyncMock()
        mock_assignment = self._make_mock_assignment()
        mock_new_assignment = MagicMock()
        mock_new_assignment.id = "assign-new"

        original_rating = self._make_mock_rating("rating-id-lama", "item-1", 4)

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment
        mock_repo.update.return_value = mock_assignment
        mock_repo.create.return_value = mock_new_assignment

        created_ratings: list = []

        async def capture_rating_create(rating: object) -> object:
            """Menangkap argumen yang diteruskan ke rating_repo.create."""
            created_ratings.append(rating)
            return rating

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = [original_rating]
        mock_rating_repo.create.side_effect = capture_rating_create

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            await service.archive_and_revise("assign-1", "admin-1")

        assert created_ratings[0].id != "rating-id-lama"

    @pytest.mark.asyncio
    async def test_archive_and_revise_deadline_dipertahankan(self) -> None:
        """assignment baru harus mewarisi deadline yang sama dari assignment lama."""
        from datetime import datetime

        mock_db = AsyncMock()
        deadline = datetime(2026, 12, 31, 23, 59, 59)
        mock_assignment = self._make_mock_assignment(deadline=deadline)
        captured: list = []

        async def capture_create(new_assign: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(new_assign)
            return new_assign

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment
        mock_repo.update.return_value = mock_assignment
        mock_repo.create.side_effect = capture_create

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = []

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            await service.archive_and_revise("assign-1", "admin-1")

        assert captured[0].deadline == deadline


class TestAssignmentRevisionSchema:
    """Kumpulan test untuk validasi schema RevisionResult."""

    def test_revision_result_dapat_dibuat_dari_dua_response(self) -> None:
        """RevisionResult harus dapat dibuat dari dua AssignmentResponse."""
        from datetime import datetime

        from app.schemas.expert_assignment import AssignmentResponse, RevisionResult

        now = datetime(2026, 6, 19, 12, 0, 0)

        archived = AssignmentResponse(
            id="assign-old",
            instrument_id="instr-1",
            instrument_name="Skala Test",
            user_id="expert-1",
            assigned_by="admin-1",
            deadline=None,
            status="archived",
            previous_assignment_id=None,
            revision_number=1,
            assigned_at=now,
            updated_at=now,
        )
        new_assign = AssignmentResponse(
            id="assign-new",
            instrument_id="instr-1",
            instrument_name="Skala Test",
            user_id="expert-1",
            assigned_by="admin-1",
            deadline=None,
            status="in_progress",
            previous_assignment_id="assign-old",
            revision_number=2,
            assigned_at=now,
            updated_at=now,
        )

        result = RevisionResult(archived_assignment=archived, new_assignment=new_assign)

        assert result.archived_assignment.status == "archived"
        assert result.new_assignment.status == "in_progress"
        assert result.new_assignment.previous_assignment_id == "assign-old"
        assert result.new_assignment.revision_number == 2

    def test_assignment_response_default_revision_number_satu(self) -> None:
        """AssignmentResponse harus memiliki revision_number default = 1."""
        from datetime import datetime

        from app.schemas.expert_assignment import AssignmentResponse

        now = datetime(2026, 6, 19, 12, 0, 0)
        response = AssignmentResponse(
            id="assign-1",
            instrument_id="instr-1",
            user_id="expert-1",
            assigned_by="admin-1",
            deadline=None,
            status="pending",
            assigned_at=now,
            updated_at=now,
        )

        assert response.revision_number == 1
        assert response.previous_assignment_id is None


class TestAssignmentRevisionModel:
    """Kumpulan test untuk kolom model ExpertAssignment yang baru."""

    def test_model_memiliki_kolom_revision_number(self) -> None:
        """ExpertAssignment harus memiliki kolom revision_number yang dapat diisi."""
        from app.models.expert_assignment import ExpertAssignment

        assignment = ExpertAssignment(
            id="assign-1",
            instrument_id="instr-1",
            user_id="expert-1",
            assigned_by="admin-1",
            revision_number=1,
        )

        assert assignment.revision_number == 1

    def test_model_memiliki_kolom_previous_assignment_id_nullable(self) -> None:
        """ExpertAssignment baru harus memiliki previous_assignment_id = None secara default."""
        from app.models.expert_assignment import ExpertAssignment

        assignment = ExpertAssignment(
            id="assign-1",
            instrument_id="instr-1",
            user_id="expert-1",
            assigned_by="admin-1",
        )

        assert assignment.previous_assignment_id is None

    def test_model_menerima_previous_assignment_id(self) -> None:
        """ExpertAssignment harus menerima previous_assignment_id saat pembuatan."""
        from app.models.expert_assignment import ExpertAssignment

        assignment = ExpertAssignment(
            id="assign-2",
            instrument_id="instr-1",
            user_id="expert-1",
            assigned_by="admin-1",
            previous_assignment_id="assign-1",
            revision_number=2,
        )

        assert assignment.previous_assignment_id == "assign-1"
        assert assignment.revision_number == 2
