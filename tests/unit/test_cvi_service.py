"""Unit test untuk fungsi-fungsi kalkulasi CVI dan CVIService (tanpa DB)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.cvi_service import (
    calculate_i_cvi,
    calculate_s_cvi_ave,
    calculate_s_cvi_ua,
    is_i_cvi_valid,
)


class TestCalculateICVI:
    """Kumpulan test untuk fungsi calculate_i_cvi."""

    def test_semua_relevan(self) -> None:
        """I-CVI = 1.0 jika semua expert memberi skor >= 3."""
        assert calculate_i_cvi([3, 4, 4, 3], n_experts=4) == 1.0

    def test_tidak_ada_yang_relevan(self) -> None:
        """I-CVI = 0.0 jika semua expert memberi skor < 3."""
        assert calculate_i_cvi([1, 2, 1, 2], n_experts=4) == 0.0

    def test_sebagian_relevan(self) -> None:
        """I-CVI = 0.75 jika 3 dari 4 expert memberi skor >= 3."""
        assert calculate_i_cvi([3, 4, 2, 4], n_experts=4) == 0.75

    def test_satu_expert(self) -> None:
        """I-CVI = 1.0 jika satu expert memberikan skor relevan."""
        assert calculate_i_cvi([4], n_experts=1) == 1.0

    def test_expert_nol_raise_valueerror(self) -> None:
        """Harus raise ValueError jika n_experts = 0."""
        with pytest.raises(ValueError):
            calculate_i_cvi([3, 4], n_experts=0)

    def test_expert_negatif_raise_valueerror(self) -> None:
        """Harus raise ValueError jika n_experts < 0."""
        with pytest.raises(ValueError):
            calculate_i_cvi([3], n_experts=-1)

    def test_skor_batas_bawah(self) -> None:
        """Skor 3 dianggap relevan (batas bawah relevansi)."""
        assert calculate_i_cvi([3], n_experts=1) == 1.0

    def test_skor_2_tidak_relevan(self) -> None:
        """Skor 2 tidak dianggap relevan."""
        assert calculate_i_cvi([2], n_experts=1) == 0.0


class TestCalculateSCVIAve:
    """Kumpulan test untuk fungsi calculate_s_cvi_ave."""

    def test_rata_rata_normal(self) -> None:
        """S-CVI/Ave = rata-rata dari semua I-CVI."""
        result = calculate_s_cvi_ave([0.8, 1.0, 0.6])
        assert abs(result - 0.8) < 1e-9

    def test_semua_sempurna(self) -> None:
        """S-CVI/Ave = 1.0 jika semua I-CVI = 1.0."""
        assert calculate_s_cvi_ave([1.0, 1.0, 1.0]) == 1.0

    def test_list_kosong(self) -> None:
        """S-CVI/Ave = 0.0 jika tidak ada item."""
        assert calculate_s_cvi_ave([]) == 0.0

    def test_satu_item(self) -> None:
        """S-CVI/Ave = nilai tunggal jika hanya satu item."""
        assert calculate_s_cvi_ave([0.75]) == 0.75


class TestCalculateSCVIUA:
    """Kumpulan test untuk fungsi calculate_s_cvi_ua."""

    def test_semua_sempurna(self) -> None:
        """S-CVI/UA = 1.0 jika semua I-CVI = 1.0."""
        assert calculate_s_cvi_ua([1.0, 1.0, 1.0]) == 1.0

    def test_tidak_ada_yang_sempurna(self) -> None:
        """S-CVI/UA = 0.0 jika tidak ada I-CVI = 1.0."""
        assert calculate_s_cvi_ua([0.8, 0.9, 0.75]) == 0.0

    def test_sebagian_sempurna(self) -> None:
        """S-CVI/UA = 2/3 jika 2 dari 3 item memiliki I-CVI = 1.0."""
        result = calculate_s_cvi_ua([1.0, 0.8, 1.0])
        assert abs(result - 2 / 3) < 1e-9

    def test_list_kosong(self) -> None:
        """S-CVI/UA = 0.0 jika tidak ada item."""
        assert calculate_s_cvi_ua([]) == 0.0


class TestIsICVIValid:
    """Kumpulan test untuk fungsi is_i_cvi_valid."""

    def test_banyak_expert_i_cvi_valid(self) -> None:
        """I-CVI >= 0.78 valid jika jumlah expert >= 8."""
        assert is_i_cvi_valid(0.78, n_experts=8) is True
        assert is_i_cvi_valid(1.0, n_experts=10) is True

    def test_banyak_expert_i_cvi_tidak_valid(self) -> None:
        """I-CVI < 0.78 tidak valid jika jumlah expert >= 8."""
        assert is_i_cvi_valid(0.77, n_experts=8) is False
        assert is_i_cvi_valid(0.5, n_experts=9) is False

    def test_sedikit_expert_harus_sempurna(self) -> None:
        """Jika expert < 8, I-CVI harus = 1.0 agar valid."""
        assert is_i_cvi_valid(1.0, n_experts=5) is True
        assert is_i_cvi_valid(0.8, n_experts=7) is False
        assert is_i_cvi_valid(0.0, n_experts=3) is False

    def test_tepat_di_batas_8_expert(self) -> None:
        """Pada batas tepat 8 expert, threshold adalah 0.78."""
        assert is_i_cvi_valid(0.78, n_experts=8) is True
        assert is_i_cvi_valid(0.77, n_experts=8) is False


class TestCVIServiceCalculate:
    """Kumpulan test untuk method CVIService.calculate()."""

    @pytest.mark.asyncio
    async def test_calculate_instrumen_tidak_ditemukan_raise_404(self) -> None:
        """calculate harus raise HTTPException 404 jika instrumen tidak ditemukan."""
        mock_db = AsyncMock()
        mock_instrument_repo = AsyncMock()
        mock_instrument_repo.get_by_id.return_value = None

        with (
            patch(
                "app.services.cvi_service.InstrumentRepository",
                return_value=mock_instrument_repo,
            ),
            patch("app.services.cvi_service.ItemRepository", return_value=AsyncMock()),
            patch(
                "app.services.cvi_service.ExpertAssignmentRepository",
                return_value=AsyncMock(),
            ),
            patch("app.services.cvi_service.RatingRepository", return_value=AsyncMock()),
        ):
            from app.services.cvi_service import CVIService

            service = CVIService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.calculate("nonexistent-id")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_calculate_instrumen_tanpa_item_raise_400(self) -> None:
        """calculate harus raise HTTPException 400 jika instrumen tidak memiliki item."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()

        mock_instrument_repo = AsyncMock()
        mock_instrument_repo.get_by_id.return_value = mock_instrument

        mock_item_repo = AsyncMock()
        mock_item_repo.get_by_instrument.return_value = []

        with (
            patch(
                "app.services.cvi_service.InstrumentRepository",
                return_value=mock_instrument_repo,
            ),
            patch("app.services.cvi_service.ItemRepository", return_value=mock_item_repo),
            patch(
                "app.services.cvi_service.ExpertAssignmentRepository",
                return_value=AsyncMock(),
            ),
            patch("app.services.cvi_service.RatingRepository", return_value=AsyncMock()),
        ):
            from app.services.cvi_service import CVIService

            service = CVIService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.calculate("instr-1")

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_calculate_belum_ada_rating_raise_400(self) -> None:
        """calculate harus raise HTTPException 400 jika belum ada penilaian."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()
        mock_item = MagicMock()

        mock_instrument_repo = AsyncMock()
        mock_instrument_repo.get_by_id.return_value = mock_instrument

        mock_item_repo = AsyncMock()
        mock_item_repo.get_by_instrument.return_value = [mock_item]

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_instrument.return_value = []

        with (
            patch(
                "app.services.cvi_service.InstrumentRepository",
                return_value=mock_instrument_repo,
            ),
            patch("app.services.cvi_service.ItemRepository", return_value=mock_item_repo),
            patch(
                "app.services.cvi_service.ExpertAssignmentRepository",
                return_value=AsyncMock(),
            ),
            patch(
                "app.services.cvi_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
        ):
            from app.services.cvi_service import CVIService

            service = CVIService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.calculate("instr-1")

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_calculate_mengembalikan_cvi_result_dengan_benar(self) -> None:
        """calculate harus mengembalikan CVIResult dengan I-CVI dan S-CVI yang tepat."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()
        mock_instrument.id = "instr-1"
        mock_instrument.name = "Instrumen A"

        item1 = MagicMock()
        item1.id = "item-1"
        item1.sequence_number = 1
        item1.content = "Pernyataan 1"
        item1.domain_id = None

        item2 = MagicMock()
        item2.id = "item-2"
        item2.sequence_number = 2
        item2.content = "Pernyataan 2"
        item2.domain_id = None

        # item-1: 2 rating relevan (skor 4 dan 3) → I-CVI = 1.0
        rating1 = MagicMock()
        rating1.item_id = "item-1"
        rating1.relevance_score = 4
        rating1.user_id = "expert-1"

        rating2 = MagicMock()
        rating2.item_id = "item-1"
        rating2.relevance_score = 3
        rating2.user_id = "expert-2"

        # item-2: 1 relevan (skor 4), 1 tidak relevan (skor 2) → I-CVI = 0.5
        rating3 = MagicMock()
        rating3.item_id = "item-2"
        rating3.relevance_score = 4
        rating3.user_id = "expert-1"

        rating4 = MagicMock()
        rating4.item_id = "item-2"
        rating4.relevance_score = 2
        rating4.user_id = "expert-2"

        mock_instrument_repo = AsyncMock()
        mock_instrument_repo.get_by_id.return_value = mock_instrument

        mock_item_repo = AsyncMock()
        mock_item_repo.get_by_instrument.return_value = [item1, item2]

        mock_rating_repo = AsyncMock()
        mock_rating_repo.get_by_instrument.return_value = [rating1, rating2, rating3, rating4]

        with (
            patch(
                "app.services.cvi_service.InstrumentRepository",
                return_value=mock_instrument_repo,
            ),
            patch("app.services.cvi_service.ItemRepository", return_value=mock_item_repo),
            patch(
                "app.services.cvi_service.ExpertAssignmentRepository",
                return_value=AsyncMock(),
            ),
            patch(
                "app.services.cvi_service.RatingRepository",
                return_value=mock_rating_repo,
            ),
        ):
            from app.services.cvi_service import CVIService

            service = CVIService(mock_db)
            result = await service.calculate("instr-1")

        assert result.instrument_id == "instr-1"
        assert result.instrument_name == "Instrumen A"
        assert result.n_items == 2
        assert result.n_experts == 2
        assert len(result.items) == 2
        assert result.items[0].i_cvi == 1.0
        assert result.items[0].is_valid is True
        assert result.items[1].i_cvi == 0.5
        # S-CVI/Ave = (1.0 + 0.5) / 2 = 0.75
        assert result.s_cvi_ave == 0.75
        # S-CVI/UA = 1/2 = 0.5 (hanya item-1 yang I-CVI = 1.0)
        assert result.s_cvi_ua == 0.5
