"""Service untuk kalkulasi Content Validity Index (CVI)."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dimension_repository import DimensionRepository
from app.repositories.expert_assignment_repository import ExpertAssignmentRepository
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.rating_repository import RatingRepository
from app.schemas.cvi import CVIResult, ItemCVIResult


def calculate_i_cvi(relevance_scores: list[int], n_experts: int) -> float:
    """Menghitung Item Content Validity Index (I-CVI) untuk satu item.

    I-CVI = jumlah expert yang memberi skor ≥3 / total expert.
    Skor 3 (cukup relevan) dan 4 (sangat relevan) dianggap relevan.

    Args:
        relevance_scores: Daftar skor relevansi dari para expert (skala 1–4).
        n_experts: Jumlah total expert yang menilai.

    Returns:
        Nilai I-CVI antara 0.0 dan 1.0.

    Raises:
        ValueError: Jika n_experts bernilai nol atau negatif.

    Example:
        >>> calculate_i_cvi([3, 4, 2, 4, 3], n_experts=5)
        0.8
    """
    if n_experts <= 0:
        raise ValueError("Jumlah expert harus lebih besar dari nol.")
    relevant_count = sum(1 for score in relevance_scores if score >= 3)
    return relevant_count / n_experts


def calculate_s_cvi_ave(i_cvi_list: list[float]) -> float:
    """Menghitung Scale Content Validity Index metode Average (S-CVI/Ave).

    S-CVI/Ave = rata-rata dari semua I-CVI item.

    Args:
        i_cvi_list: Daftar nilai I-CVI dari semua item dalam instrumen.

    Returns:
        Nilai S-CVI/Ave antara 0.0 dan 1.0, atau 0.0 jika tidak ada item.

    Example:
        >>> calculate_s_cvi_ave([0.8, 1.0, 0.6])
        0.8
    """
    if not i_cvi_list:
        return 0.0
    return sum(i_cvi_list) / len(i_cvi_list)


def calculate_s_cvi_ua(i_cvi_list: list[float]) -> float:
    """Menghitung Scale Content Validity Index metode Universal Agreement (S-CVI/UA).

    S-CVI/UA = proporsi item di mana semua expert sepakat relevan (I-CVI = 1.0).

    Args:
        i_cvi_list: Daftar nilai I-CVI dari semua item dalam instrumen.

    Returns:
        Nilai S-CVI/UA antara 0.0 dan 1.0, atau 0.0 jika tidak ada item.

    Example:
        >>> calculate_s_cvi_ua([1.0, 0.8, 1.0])
        0.6666666666666666
    """
    if not i_cvi_list:
        return 0.0
    perfect_items = sum(1 for i_cvi in i_cvi_list if i_cvi == 1.0)
    return perfect_items / len(i_cvi_list)


def is_i_cvi_valid(i_cvi: float, n_experts: int) -> bool:
    """Menentukan apakah nilai I-CVI memenuhi threshold validitas.

    Threshold:
        - Jika jumlah expert < 8: I-CVI harus = 1.0
        - Jika jumlah expert ≥ 8: I-CVI harus ≥ 0.78

    Args:
        i_cvi: Nilai I-CVI item.
        n_experts: Jumlah total expert.

    Returns:
        True jika I-CVI memenuhi threshold, False jika tidak.

    Example:
        >>> is_i_cvi_valid(0.8, 10)
        True
        >>> is_i_cvi_valid(0.8, 5)
        False
    """
    if n_experts < 8:
        return i_cvi == 1.0
    return i_cvi >= 0.78


class CVIService:
    """Service yang menghitung Content Validity Index untuk sebuah instrumen.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi CVIService.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db
        self.instrument_repo = InstrumentRepository(db)
        self.item_repo = ItemRepository(db)
        self.assignment_repo = ExpertAssignmentRepository(db)
        self.rating_repo = RatingRepository(db)

    async def calculate(self, instrument_id: str) -> CVIResult:
        """Menghitung hasil CVI lengkap untuk sebuah instrumen.

        Mengambil semua rating dari seluruh expert yang ditugaskan,
        lalu menghitung I-CVI per item serta S-CVI/Ave dan S-CVI/UA.

        Args:
            instrument_id: ID instrumen yang akan dikalkulasi.

        Returns:
            Objek CVIResult berisi I-CVI per item dan S-CVI keseluruhan.

        Raises:
            HTTPException: Jika instrumen tidak ditemukan (404) atau belum ada rating (400).
        """
        instrument = await self.instrument_repo.get_by_id(instrument_id)
        if not instrument:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instrumen '{instrument_id}' tidak ditemukan.",
            )

        items = await self.item_repo.get_by_instrument(instrument_id)
        if not items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instrumen tidak memiliki item.",
            )

        all_ratings = await self.rating_repo.get_by_instrument(instrument_id)
        if not all_ratings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Belum ada penilaian yang diberikan untuk instrumen ini.",
            )

        # Kelompokkan rating berdasarkan item_id
        ratings_by_item: dict[str, list[int]] = {item.id: [] for item in items}
        expert_ids: set[str] = set()
        for rating in all_ratings:
            if rating.item_id in ratings_by_item:
                ratings_by_item[rating.item_id].append(rating.relevance_score)
                expert_ids.add(rating.user_id)

        n_experts = len(expert_ids)
        item_results: list[ItemCVIResult] = []

        # Ambil semua dimensi untuk mendapatkan nama dimensi per item
        dim_repo = DimensionRepository(self.db)
        dimensions = await dim_repo.get_by_instrument(instrument_id)
        dim_map = {d.id: d.name for d in dimensions}

        for item in items:
            scores = ratings_by_item[item.id]
            n_rated = len(scores)
            if n_rated == 0:
                i_cvi_val = 0.0
                n_relevant = 0
            else:
                i_cvi_val = calculate_i_cvi(scores, n_rated)
                n_relevant = sum(1 for s in scores if s >= 3)

            item_results.append(
                ItemCVIResult(
                    item_id=item.id,
                    sequence_number=item.sequence_number,
                    content=item.content,
                    dimension_name=dim_map.get(item.dimension_id) if item.dimension_id else None,
                    n_experts=n_rated,
                    n_relevant=n_relevant,
                    i_cvi=round(i_cvi_val, 4),
                    is_valid=is_i_cvi_valid(i_cvi_val, n_rated),
                )
            )

        i_cvi_values = [r.i_cvi for r in item_results]
        return CVIResult(
            instrument_id=instrument_id,
            instrument_name=instrument.name,
            n_experts=n_experts,
            n_items=len(items),
            items=item_results,
            s_cvi_ave=round(calculate_s_cvi_ave(i_cvi_values), 4),
            s_cvi_ua=round(calculate_s_cvi_ua(i_cvi_values), 4),
        )
