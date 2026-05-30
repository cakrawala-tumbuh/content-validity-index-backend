"""Repository untuk operasi database entitas ExpertAssignment."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expert_assignment import ExpertAssignment


class ExpertAssignmentRepository:
    """Repository untuk operasi CRUD pada tabel expert_assignments.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi ExpertAssignmentRepository.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db

    async def get_by_id(self, assignment_id: str) -> ExpertAssignment | None:
        """Mengambil assignment berdasarkan ID.

        Args:
            assignment_id: ID unik assignment.

        Returns:
            Instance ExpertAssignment jika ditemukan, None jika tidak.
        """
        result = await self.db.execute(
            select(ExpertAssignment).where(ExpertAssignment.id == assignment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_instrument(self, instrument_id: str) -> list[ExpertAssignment]:
        """Mengambil semua assignment untuk sebuah instrumen.

        Args:
            instrument_id: ID instrumen.

        Returns:
            Daftar ExpertAssignment untuk instrumen tersebut.
        """
        result = await self.db.execute(
            select(ExpertAssignment).where(
                ExpertAssignment.instrument_id == instrument_id
            )
        )
        return list(result.scalars().all())

    async def get_by_user(self, user_id: str) -> list[ExpertAssignment]:
        """Mengambil semua assignment milik seorang expert.

        Args:
            user_id: ID expert.

        Returns:
            Daftar ExpertAssignment milik expert tersebut.
        """
        result = await self.db.execute(
            select(ExpertAssignment).where(ExpertAssignment.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_by_instrument_and_user(
        self, instrument_id: str, user_id: str
    ) -> ExpertAssignment | None:
        """Mengambil assignment berdasarkan instrumen dan user.

        Args:
            instrument_id: ID instrumen.
            user_id: ID expert.

        Returns:
            Instance ExpertAssignment jika ditemukan, None jika tidak.
        """
        result = await self.db.execute(
            select(ExpertAssignment).where(
                ExpertAssignment.instrument_id == instrument_id,
                ExpertAssignment.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, assignment: ExpertAssignment) -> ExpertAssignment:
        """Menyimpan assignment baru ke database.

        Args:
            assignment: Instance ExpertAssignment yang akan disimpan.

        Returns:
            Instance ExpertAssignment yang sudah disimpan.
        """
        self.db.add(assignment)
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment

    async def update(self, assignment: ExpertAssignment) -> ExpertAssignment:
        """Memperbarui data assignment di database.

        Args:
            assignment: Instance ExpertAssignment dengan data yang sudah diubah.

        Returns:
            Instance ExpertAssignment yang sudah diperbarui.
        """
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment

    async def delete(self, assignment: ExpertAssignment) -> None:
        """Menghapus assignment dari database.

        Args:
            assignment: Instance ExpertAssignment yang akan dihapus.
        """
        await self.db.delete(assignment)
        await self.db.flush()
