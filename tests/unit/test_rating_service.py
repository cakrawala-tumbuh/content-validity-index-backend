"""Unit test untuk RatingService — validasi kepemilikan, get, dan update rating."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.rating import RatingBulkCreate, RatingItem, RatingUpdate


class TestRatingItemSchema:
    """Kumpulan test untuk validasi catatan wajib pada RatingItem."""

    @pytest.mark.parametrize("score", [1, 2])
    def test_skor_rendah_tanpa_catatan_raise_validation_error(self, score: int) -> None:
        """RatingItem dengan skor 1/2 tanpa catatan harus gagal validasi."""
        with pytest.raises(ValidationError):
            RatingItem(item_id="item-1", relevance_score=score, notes=None)

    @pytest.mark.parametrize("score", [1, 2])
    def test_skor_rendah_catatan_spasi_raise_validation_error(self, score: int) -> None:
        """RatingItem dengan skor 1/2 dan catatan hanya spasi harus gagal validasi."""
        with pytest.raises(ValidationError):
            RatingItem(item_id="item-1", relevance_score=score, notes="   ")

    @pytest.mark.parametrize("score", [1, 2])
    def test_skor_rendah_dengan_catatan_valid(self, score: int) -> None:
        """RatingItem dengan skor 1/2 dan catatan terisi harus valid."""
        item = RatingItem(item_id="item-1", relevance_score=score, notes="Perlu revisi.")
        assert item.relevance_score == score

    @pytest.mark.parametrize("score", [3, 4])
    def test_skor_tinggi_tanpa_catatan_valid(self, score: int) -> None:
        """RatingItem dengan skor 3/4 tanpa catatan harus tetap valid."""
        item = RatingItem(item_id="item-1", relevance_score=score, notes=None)
        assert item.notes is None


class TestRatingServiceValidation:
    """Kumpulan test untuk validasi kepemilikan assignment di RatingService."""

    @pytest.mark.asyncio
    async def test_bulk_submit_assignment_tidak_ditemukan(self) -> None:
        """bulk_submit harus raise 404 jika assignment tidak ditemukan."""
        mock_db = AsyncMock()
        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_id.return_value = None

        with (
            patch(
                "app.services.rating_service.ExpertAssignmentRepository",
                return_value=mock_assignment_repo,
            ),
            patch(
                "app.services.rating_service.RatingRepository",
                return_value=AsyncMock(),
            ),
            patch(
                "app.services.rating_service.ItemRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            data = RatingBulkCreate(ratings=[RatingItem(item_id="item-1", relevance_score=4)])

            with pytest.raises(HTTPException) as exc_info:
                await service.bulk_submit("nonexistent-id", "user-1", data)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_bulk_submit_bukan_expert_yang_ditugaskan(self) -> None:
        """bulk_submit harus raise 403 jika user bukan expert yang di-assign."""
        mock_db = AsyncMock()
        mock_assignment = MagicMock()
        mock_assignment.user_id = "other-user"

        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_id.return_value = mock_assignment

        with (
            patch(
                "app.services.rating_service.ExpertAssignmentRepository",
                return_value=mock_assignment_repo,
            ),
            patch(
                "app.services.rating_service.RatingRepository",
                return_value=AsyncMock(),
            ),
            patch(
                "app.services.rating_service.ItemRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            data = RatingBulkCreate(ratings=[RatingItem(item_id="item-1", relevance_score=4)])

            with pytest.raises(HTTPException) as exc_info:
                await service.bulk_submit("assignment-1", "user-yang-salah", data)
            assert exc_info.value.status_code == 403


class TestRatingServiceGetByAssignment:
    """Kumpulan test untuk method RatingService.get_by_assignment()."""

    @pytest.mark.asyncio
    async def test_admin_mendapat_rating_tanpa_validasi_kepemilikan(self) -> None:
        """Admin harus bisa mengakses rating tanpa pengecekan kepemilikan assignment."""
        mock_db = AsyncMock()
        mock_ratings = [MagicMock(), MagicMock()]

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = mock_ratings

        mock_assignment_repo = AsyncMock()

        with (
            patch(
                "app.services.rating_service.ExpertAssignmentRepository",
                return_value=mock_assignment_repo,
            ),
            patch(
                "app.services.rating_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.rating_service.ItemRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            result = await service.get_by_assignment("assign-1", "admin-1", "admin")

        mock_assignment_repo.get_by_id.assert_not_called()
        mock_rating_repo.get_by_assignment.assert_called_once_with("assign-1")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_expert_pemilik_dapat_mengakses_ratingnya(self) -> None:
        """Expert yang memiliki assignment harus bisa mengakses ratingnya."""
        mock_db = AsyncMock()
        mock_assignment = MagicMock()
        mock_assignment.user_id = "expert-1"
        mock_ratings = [MagicMock()]

        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_id.return_value = mock_assignment

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.return_value = mock_ratings

        with (
            patch(
                "app.services.rating_service.ExpertAssignmentRepository",
                return_value=mock_assignment_repo,
            ),
            patch(
                "app.services.rating_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.rating_service.ItemRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            result = await service.get_by_assignment("assign-1", "expert-1", "expert")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_expert_lain_raise_403(self) -> None:
        """Expert yang bukan pemilik assignment harus mendapat HTTPException 403."""
        mock_db = AsyncMock()
        mock_assignment = MagicMock()
        mock_assignment.user_id = "expert-lain"

        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_id.return_value = mock_assignment

        with (
            patch(
                "app.services.rating_service.ExpertAssignmentRepository",
                return_value=mock_assignment_repo,
            ),
            patch(
                "app.services.rating_service.RatingRepository",
                return_value=AsyncMock(),
            ),
            patch(
                "app.services.rating_service.ItemRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.get_by_assignment("assign-1", "expert-1", "expert")

        assert exc_info.value.status_code == 403


class TestRatingServiceUpdateSingle:
    """Kumpulan test untuk method RatingService.update_single()."""

    @pytest.mark.asyncio
    async def test_update_single_berhasil_memperbarui_rating(self) -> None:
        """update_single harus memperbarui score dan notes lalu memanggil repo.update."""
        mock_db = AsyncMock()
        mock_assignment = MagicMock()
        mock_assignment.user_id = "expert-1"

        mock_rating = MagicMock()
        mock_rating.id = "rating-1"
        mock_rating.assignment_id = "assign-1"
        mock_rating.user_id = "expert-1"
        mock_rating.relevance_score = 2
        mock_rating.notes = None

        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_id.return_value = mock_assignment

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_id.return_value = mock_rating
        mock_rating_repo.update.return_value = mock_rating

        with (
            patch(
                "app.services.rating_service.ExpertAssignmentRepository",
                return_value=mock_assignment_repo,
            ),
            patch(
                "app.services.rating_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.rating_service.ItemRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            data = RatingUpdate(relevance_score=4, notes="Sangat relevan")
            result = await service.update_single("assign-1", "rating-1", "expert-1", data)

        assert mock_rating.relevance_score == 4
        assert mock_rating.notes == "Sangat relevan"
        mock_rating_repo.update.assert_called_once_with(mock_rating)
        assert result is mock_rating

    @pytest.mark.asyncio
    async def test_update_single_skor_rendah_tanpa_catatan_raise_400(self) -> None:
        """update_single harus raise 400 jika skor akhir 1/2 tetapi catatan kosong."""
        mock_db = AsyncMock()
        mock_assignment = MagicMock()
        mock_assignment.user_id = "expert-1"

        mock_rating = MagicMock()
        mock_rating.id = "rating-1"
        mock_rating.assignment_id = "assign-1"
        mock_rating.user_id = "expert-1"
        mock_rating.relevance_score = 4
        mock_rating.notes = None

        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_id.return_value = mock_assignment

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_id.return_value = mock_rating

        with (
            patch(
                "app.services.rating_service.ExpertAssignmentRepository",
                return_value=mock_assignment_repo,
            ),
            patch(
                "app.services.rating_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.rating_service.ItemRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.update_single(
                    "assign-1", "rating-1", "expert-1", RatingUpdate(relevance_score=2)
                )

        assert exc_info.value.status_code == 400
        mock_rating_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_single_skor_rendah_dengan_catatan_berhasil(self) -> None:
        """update_single harus berhasil jika skor 1/2 disertai catatan."""
        mock_db = AsyncMock()
        mock_assignment = MagicMock()
        mock_assignment.user_id = "expert-1"

        mock_rating = MagicMock()
        mock_rating.id = "rating-1"
        mock_rating.assignment_id = "assign-1"
        mock_rating.user_id = "expert-1"
        mock_rating.relevance_score = 4
        mock_rating.notes = None

        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_id.return_value = mock_assignment

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_id.return_value = mock_rating
        mock_rating_repo.update.return_value = mock_rating

        with (
            patch(
                "app.services.rating_service.ExpertAssignmentRepository",
                return_value=mock_assignment_repo,
            ),
            patch(
                "app.services.rating_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.rating_service.ItemRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            data = RatingUpdate(relevance_score=1, notes="Tidak sesuai konstruk.")
            await service.update_single("assign-1", "rating-1", "expert-1", data)

        assert mock_rating.relevance_score == 1
        assert mock_rating.notes == "Tidak sesuai konstruk."
        mock_rating_repo.update.assert_called_once_with(mock_rating)

    @pytest.mark.asyncio
    async def test_update_single_rating_tidak_ditemukan_raise_404(self) -> None:
        """update_single harus raise HTTPException 404 jika rating tidak ada."""
        mock_db = AsyncMock()
        mock_assignment = MagicMock()
        mock_assignment.user_id = "expert-1"

        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_id.return_value = mock_assignment

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_id.return_value = None

        with (
            patch(
                "app.services.rating_service.ExpertAssignmentRepository",
                return_value=mock_assignment_repo,
            ),
            patch(
                "app.services.rating_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.rating_service.ItemRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.update_single(
                    "assign-1", "nonexistent", "expert-1", RatingUpdate(relevance_score=3)
                )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_single_bukan_milik_user_raise_403(self) -> None:
        """update_single harus raise HTTPException 403 jika rating bukan milik user."""
        mock_db = AsyncMock()
        mock_assignment = MagicMock()
        mock_assignment.user_id = "expert-1"

        mock_rating = MagicMock()
        mock_rating.id = "rating-1"
        mock_rating.assignment_id = "assign-1"
        mock_rating.user_id = "expert-lain"

        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_id.return_value = mock_assignment

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_id.return_value = mock_rating

        with (
            patch(
                "app.services.rating_service.ExpertAssignmentRepository",
                return_value=mock_assignment_repo,
            ),
            patch(
                "app.services.rating_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
            patch(
                "app.services.rating_service.ItemRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.update_single(
                    "assign-1", "rating-1", "expert-1", RatingUpdate(relevance_score=3)
                )

        assert exc_info.value.status_code == 403


class TestRatingServiceGetExpertRatings:
    """Kumpulan test untuk method RatingService.get_expert_ratings_for_instrument()."""

    def _make_patches(
        self,
        instrument: object,
        items: list,
        assignments: list,
        users: list,
        ratings_per_assignment: dict,
    ) -> tuple:
        """Membuat mock repository lengkap untuk get_expert_ratings_for_instrument.

        Args:
            instrument: Mock instrumen (atau None jika tidak ditemukan).
            items: Daftar mock item instrumen.
            assignments: Daftar mock assignment expert.
            users: Daftar mock user expert.
            ratings_per_assignment: Dict {assignment_id: [mock_rating]}.

        Returns:
            Tuple (instrument_repo, item_repo, assignment_repo, user_repo, rating_repo).
        """
        mock_instrument_repo = AsyncMock()
        mock_instrument_repo.get_by_id.return_value = instrument

        mock_item_repo = AsyncMock()
        mock_item_repo.get_by_instrument.return_value = items

        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_instrument.return_value = assignments

        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_ids.return_value = users

        async def _get_ratings(assignment_id: str) -> list:
            return ratings_per_assignment.get(assignment_id, [])

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_assignment.side_effect = _get_ratings

        return (
            mock_instrument_repo,
            mock_item_repo,
            mock_assignment_repo,
            mock_user_repo,
            mock_rating_repo,
        )

    @pytest.mark.asyncio
    async def test_instrumen_tidak_ditemukan_raise_404(self) -> None:
        """Harus raise 404 jika instrumen tidak ditemukan."""
        mock_db = AsyncMock()
        repos = self._make_patches(None, [], [], [], {})

        with (
            patch("app.services.rating_service.InstrumentRepository", return_value=repos[0]),
            patch("app.services.rating_service.ItemRepository", return_value=repos[1]),
            patch("app.services.rating_service.ExpertAssignmentRepository", return_value=repos[2]),
            patch("app.services.rating_service.UserRepository", return_value=repos[3]),
            patch("app.services.rating_service.RatingRepository", return_value=repos[4]),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.get_expert_ratings_for_instrument("nonexistent")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_tanpa_assignment_menghasilkan_experts_kosong(self) -> None:
        """Instrumen tanpa assignment harus mengembalikan experts = []."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()
        mock_instrument.id = "inst-1"
        mock_instrument.name = "Instrumen Test"
        repos = self._make_patches(mock_instrument, [], [], [], {})

        with (
            patch("app.services.rating_service.InstrumentRepository", return_value=repos[0]),
            patch("app.services.rating_service.ItemRepository", return_value=repos[1]),
            patch("app.services.rating_service.ExpertAssignmentRepository", return_value=repos[2]),
            patch("app.services.rating_service.UserRepository", return_value=repos[3]),
            patch("app.services.rating_service.RatingRepository", return_value=repos[4]),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            result = await service.get_expert_ratings_for_instrument("inst-1")

        assert result.instrument_name == "Instrumen Test"
        assert result.n_experts == 0
        assert result.experts == []

    @pytest.mark.asyncio
    async def test_item_belum_dinilai_menghasilkan_skor_none(self) -> None:
        """Item yang belum dinilai harus memiliki relevance_score dan is_relevant None."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()
        mock_instrument.id = "inst-1"
        mock_instrument.name = "Instrumen Test"

        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.sequence_number = 1
        mock_item.content = "Teks item satu"
        mock_item.domain_id = None

        mock_assignment = MagicMock()
        mock_assignment.id = "assign-1"
        mock_assignment.user_id = "user-1"
        mock_assignment.status = "pending"
        mock_assignment.deadline = None

        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.full_name = "Dr. Ahli"
        mock_user.institution = "Universitas X"

        repos = self._make_patches(
            mock_instrument, [mock_item], [mock_assignment], [mock_user], {"assign-1": []}
        )

        with (
            patch("app.services.rating_service.InstrumentRepository", return_value=repos[0]),
            patch("app.services.rating_service.ItemRepository", return_value=repos[1]),
            patch("app.services.rating_service.ExpertAssignmentRepository", return_value=repos[2]),
            patch("app.services.rating_service.UserRepository", return_value=repos[3]),
            patch("app.services.rating_service.RatingRepository", return_value=repos[4]),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            result = await service.get_expert_ratings_for_instrument("inst-1")

        expert = result.experts[0]
        assert expert.expert_name == "Dr. Ahli"
        assert expert.institution == "Universitas X"
        item_rating = expert.ratings[0]
        assert item_rating.relevance_score is None
        assert item_rating.is_relevant is None

    @pytest.mark.asyncio
    async def test_item_dinilai_relevan_menghasilkan_is_relevant_true(self) -> None:
        """Item dengan skor >= 3 harus menghasilkan is_relevant = True."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()
        mock_instrument.id = "inst-1"
        mock_instrument.name = "Instrumen Test"

        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.sequence_number = 1
        mock_item.content = "Teks item"
        mock_item.domain_id = None

        mock_assignment = MagicMock()
        mock_assignment.id = "assign-1"
        mock_assignment.user_id = "user-1"
        mock_assignment.status = "completed"
        mock_assignment.deadline = None

        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.full_name = "Dr. Ahli"
        mock_user.institution = None

        mock_rating = MagicMock()
        mock_rating.item_id = "item-1"
        mock_rating.relevance_score = 4
        mock_rating.notes = None

        repos = self._make_patches(
            mock_instrument,
            [mock_item],
            [mock_assignment],
            [mock_user],
            {"assign-1": [mock_rating]},
        )

        with (
            patch("app.services.rating_service.InstrumentRepository", return_value=repos[0]),
            patch("app.services.rating_service.ItemRepository", return_value=repos[1]),
            patch("app.services.rating_service.ExpertAssignmentRepository", return_value=repos[2]),
            patch("app.services.rating_service.UserRepository", return_value=repos[3]),
            patch("app.services.rating_service.RatingRepository", return_value=repos[4]),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            result = await service.get_expert_ratings_for_instrument("inst-1")

        item_rating = result.experts[0].ratings[0]
        assert item_rating.relevance_score == 4
        assert item_rating.is_relevant is True

    @pytest.mark.asyncio
    async def test_experts_diurutkan_berdasarkan_nama(self) -> None:
        """Daftar expert harus diurutkan secara alfabet berdasarkan nama lengkap."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()
        mock_instrument.id = "inst-1"
        mock_instrument.name = "Instrumen Test"

        mock_assignment_1 = MagicMock()
        mock_assignment_1.id = "assign-1"
        mock_assignment_1.user_id = "user-1"
        mock_assignment_1.status = "completed"
        mock_assignment_1.deadline = None

        mock_assignment_2 = MagicMock()
        mock_assignment_2.id = "assign-2"
        mock_assignment_2.user_id = "user-2"
        mock_assignment_2.status = "pending"
        mock_assignment_2.deadline = None

        mock_user_z = MagicMock()
        mock_user_z.id = "user-1"
        mock_user_z.full_name = "Zulkifli"
        mock_user_z.institution = None

        mock_user_a = MagicMock()
        mock_user_a.id = "user-2"
        mock_user_a.full_name = "Ahmad"
        mock_user_a.institution = None

        repos = self._make_patches(
            mock_instrument,
            [],
            [mock_assignment_1, mock_assignment_2],
            [mock_user_z, mock_user_a],
            {},
        )

        with (
            patch("app.services.rating_service.InstrumentRepository", return_value=repos[0]),
            patch("app.services.rating_service.ItemRepository", return_value=repos[1]),
            patch("app.services.rating_service.ExpertAssignmentRepository", return_value=repos[2]),
            patch("app.services.rating_service.UserRepository", return_value=repos[3]),
            patch("app.services.rating_service.RatingRepository", return_value=repos[4]),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            result = await service.get_expert_ratings_for_instrument("inst-1")

        assert result.experts[0].expert_name == "Ahmad"
        assert result.experts[1].expert_name == "Zulkifli"
