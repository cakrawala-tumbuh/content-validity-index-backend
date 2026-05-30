"""Service untuk pengelolaan ExpertAssignment."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expert_assignment import ExpertAssignment
from app.repositories.expert_assignment_repository import ExpertAssignmentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.expert_assignment import AssignmentCreate


class ExpertAssignmentService:
    """Service yang menangani business logic untuk entitas ExpertAssignment.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi ExpertAssignmentService.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db
        self.repo = ExpertAssignmentRepository(db)
        self.user_repo = UserRepository(db)

    async def get_by_instrument(self, instrument_id: str) -> list[ExpertAssignment]:
        """Mengambil semua assignment untuk sebuah instrumen.

        Args:
            instrument_id: ID instrumen.

        Returns:
            Daftar ExpertAssignment.
        """
        return await self.repo.get_by_instrument(instrument_id)

    async def get_my_assignments(self, user_id: str) -> list[ExpertAssignment]:
        """Mengambil semua assignment milik expert yang sedang login.

        Args:
            user_id: ID expert.

        Returns:
            Daftar ExpertAssignment milik expert tersebut.
        """
        return await self.repo.get_by_user(user_id)

    async def get_by_id(self, assignment_id: str) -> ExpertAssignment:
        """Mengambil assignment berdasarkan ID.

        Args:
            assignment_id: ID unik assignment.

        Returns:
            Instance ExpertAssignment.

        Raises:
            HTTPException: Jika assignment tidak ditemukan (404).
        """
        assignment = await self.repo.get_by_id(assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment dengan ID '{assignment_id}' tidak ditemukan.",
            )
        return assignment

    async def create(
        self, instrument_id: str, data: AssignmentCreate, assigned_by: str
    ) -> ExpertAssignment:
        """Menugaskan expert ke sebuah instrumen.

        Args:
            instrument_id: ID instrumen tujuan.
            data: Data assignment (user_id, deadline).
            assigned_by: ID admin yang melakukan assign.

        Returns:
            Instance ExpertAssignment yang sudah dibuat.

        Raises:
            HTTPException: Jika expert tidak ditemukan (404) atau sudah ditugaskan (409).
        """
        expert = await self.user_repo.get_by_id(data.user_id)
        if not expert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User dengan ID '{data.user_id}' tidak ditemukan.",
            )
        if expert.role != "expert":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User yang ditugaskan harus memiliki role expert.",
            )

        existing = await self.repo.get_by_instrument_and_user(instrument_id, data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Expert sudah ditugaskan ke instrumen ini.",
            )

        assignment = ExpertAssignment(
            id=str(uuid.uuid4()),
            instrument_id=instrument_id,
            user_id=data.user_id,
            assigned_by=assigned_by,
            deadline=data.deadline,
        )
        return await self.repo.create(assignment)

    async def delete(self, assignment_id: str) -> None:
        """Membatalkan penugasan expert.

        Args:
            assignment_id: ID assignment yang akan dihapus.

        Raises:
            HTTPException: Jika assignment tidak ditemukan (404).
        """
        assignment = await self.get_by_id(assignment_id)
        await self.repo.delete(assignment)
