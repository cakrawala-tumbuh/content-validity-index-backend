"""Repository untuk operasi database entitas Rating."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rating import Rating


class RatingRepository:
    """Repository untuk operasi CRUD pada tabel ratings.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi RatingRepository.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db

    async def get_by_id(self, rating_id: str) -> Rating | None:
        """Mengambil rating berdasarkan ID.

        Args:
            rating_id: ID unik rating.

        Returns:
            Instance Rating jika ditemukan, None jika tidak.
        """
        result = await self.db.execute(select(Rating).where(Rating.id == rating_id))
        return result.scalar_one_or_none()

    async def get_by_assignment(self, assignment_id: str) -> list[Rating]:
        """Mengambil semua rating untuk sebuah assignment.

        Args:
            assignment_id: ID assignment.

        Returns:
            Daftar Rating untuk assignment tersebut.
        """
        result = await self.db.execute(select(Rating).where(Rating.assignment_id == assignment_id))
        return list(result.scalars().all())

    async def get_by_assignment_and_item(self, assignment_id: str, item_id: str) -> Rating | None:
        """Mengambil rating berdasarkan assignment dan item.

        Args:
            assignment_id: ID assignment.
            item_id: ID item.

        Returns:
            Instance Rating jika ditemukan, None jika tidak.
        """
        result = await self.db.execute(
            select(Rating).where(
                Rating.assignment_id == assignment_id,
                Rating.item_id == item_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_instrument(self, instrument_id: str) -> list[Rating]:
        """Mengambil semua rating untuk sebuah instrumen (dari semua expert).

        Args:
            instrument_id: ID instrumen.

        Returns:
            Daftar Rating untuk instrumen tersebut.
        """
        from app.models.expert_assignment import ExpertAssignment

        result = await self.db.execute(
            select(Rating)
            .join(ExpertAssignment, ExpertAssignment.id == Rating.assignment_id)
            .where(ExpertAssignment.instrument_id == instrument_id)
        )
        return list(result.scalars().all())

    async def create(self, rating: Rating) -> Rating:
        """Menyimpan rating baru ke database.

        Args:
            rating: Instance Rating yang akan disimpan.

        Returns:
            Instance Rating yang sudah disimpan.
        """
        self.db.add(rating)
        await self.db.flush()
        await self.db.refresh(rating)
        return rating

    async def update(self, rating: Rating) -> Rating:
        """Memperbarui data rating di database.

        Args:
            rating: Instance Rating dengan data yang sudah diubah.

        Returns:
            Instance Rating yang sudah diperbarui.
        """
        await self.db.flush()
        await self.db.refresh(rating)
        return rating
