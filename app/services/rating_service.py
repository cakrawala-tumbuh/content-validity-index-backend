"""Service untuk pengelolaan Rating (penilaian expert)."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rating import Rating
from app.repositories.expert_assignment_repository import ExpertAssignmentRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.rating_repository import RatingRepository
from app.schemas.rating import (
    NOTES_REQUIRED_MESSAGE,
    RatingBulkCreate,
    RatingUpdate,
    is_notes_missing,
)


class RatingService:
    """Service yang menangani business logic untuk entitas Rating.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi RatingService.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db
        self.repo = RatingRepository(db)
        self.assignment_repo = ExpertAssignmentRepository(db)
        self.item_repo = ItemRepository(db)

    async def _validate_assignment_ownership(self, assignment_id: str, user_id: str) -> None:
        """Memvalidasi bahwa assignment dimiliki oleh user yang sedang login.

        Args:
            assignment_id: ID assignment.
            user_id: ID user yang sedang login.

        Raises:
            HTTPException: Jika assignment tidak ditemukan (404) atau bukan milik user (403).
        """
        assignment = await self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment dengan ID '{assignment_id}' tidak ditemukan.",
            )
        if assignment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses ke assignment ini.",
            )

    async def get_by_assignment(self, assignment_id: str, user_id: str, role: str) -> list[Rating]:
        """Mengambil semua rating untuk sebuah assignment.

        Expert hanya bisa melihat rating miliknya sendiri.
        Admin bisa melihat semua rating.

        Args:
            assignment_id: ID assignment.
            user_id: ID user yang meminta.
            role: Role user (admin/expert).

        Returns:
            Daftar Rating.

        Raises:
            HTTPException: Jika expert tidak punya akses ke assignment (403).
        """
        if role != "admin":
            await self._validate_assignment_ownership(assignment_id, user_id)
        return await self.repo.get_by_assignment(assignment_id)

    async def bulk_submit(
        self, assignment_id: str, user_id: str, data: RatingBulkCreate
    ) -> list[Rating]:
        """Submit semua penilaian untuk sebuah assignment sekaligus.

        Jika rating untuk item tertentu sudah ada, rating tersebut diperbarui.
        Jika belum ada, rating baru dibuat.

        Args:
            assignment_id: ID assignment.
            user_id: ID expert yang memberikan penilaian.
            data: Data penilaian bulk.

        Returns:
            Daftar Rating yang sudah dibuat/diperbarui.

        Raises:
            HTTPException: Jika assignment tidak ditemukan/bukan milik user (403/404),
                           atau instrumen tidak aktif (400), atau item tidak valid (400).
        """
        await self._validate_assignment_ownership(assignment_id, user_id)

        assignment = await self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment tidak ditemukan.",
            )

        # Ambil semua item valid untuk instrumen ini
        valid_items = await self.item_repo.get_by_instrument(assignment.instrument_id)
        valid_item_ids = {item.id for item in valid_items}

        results: list[Rating] = []
        for rating_data in data.ratings:
            if rating_data.item_id not in valid_item_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item '{rating_data.item_id}' tidak ditemukan dalam instrumen ini.",
                )

            existing = await self.repo.get_by_assignment_and_item(
                assignment_id, rating_data.item_id
            )
            if existing:
                existing.relevance_score = rating_data.relevance_score
                existing.notes = rating_data.notes
                updated = await self.repo.update(existing)
                results.append(updated)
            else:
                new_rating = Rating(
                    id=str(uuid.uuid4()),
                    assignment_id=assignment_id,
                    item_id=rating_data.item_id,
                    user_id=user_id,
                    relevance_score=rating_data.relevance_score,
                    notes=rating_data.notes,
                )
                created = await self.repo.create(new_rating)
                results.append(created)

        # Perbarui status assignment menjadi in_progress jika masih pending
        if assignment.status == "pending":
            assignment.status = "in_progress"
            await self.assignment_repo.update(assignment)

        # Cek apakah semua item sudah dinilai → tandai completed
        all_ratings = await self.repo.get_by_assignment(assignment_id)
        if len(all_ratings) >= len(valid_item_ids):
            assignment.status = "completed"
            await self.assignment_repo.update(assignment)

        return results

    async def update_single(
        self, assignment_id: str, rating_id: str, user_id: str, data: RatingUpdate
    ) -> Rating:
        """Memperbarui satu rating.

        Expert hanya bisa memperbarui rating miliknya sendiri.

        Args:
            assignment_id: ID assignment tempat rating berada.
            rating_id: ID rating yang akan diperbarui.
            user_id: ID expert yang memperbarui.
            data: Data pembaruan rating.

        Returns:
            Instance Rating yang sudah diperbarui.

        Raises:
            HTTPException: Jika rating tidak ditemukan (404), tidak memiliki akses (403),
                           atau catatan kosong padahal skor akhir 1/2 (400).
        """
        await self._validate_assignment_ownership(assignment_id, user_id)

        rating = await self.repo.get_by_id(rating_id)
        if not rating or rating.assignment_id != assignment_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rating dengan ID '{rating_id}' tidak ditemukan.",
            )
        if rating.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak dapat memperbarui rating ini.",
            )

        if data.relevance_score is not None:
            rating.relevance_score = data.relevance_score
        if data.notes is not None:
            rating.notes = data.notes

        # Catatan wajib diisi jika skor akhir bernilai 1 atau 2.
        if is_notes_missing(rating.relevance_score, rating.notes):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=NOTES_REQUIRED_MESSAGE,
            )
        return await self.repo.update(rating)
