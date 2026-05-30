"""Unit test untuk fungsi-fungsi kalkulasi CVI murni (tanpa DB)."""

import pytest

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
