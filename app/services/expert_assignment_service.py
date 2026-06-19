"""Service untuk pengelolaan ExpertAssignment."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expert_assignment import ExpertAssignment
from app.models.rating import Rating
from app.repositories.expert_assignment_repository import ExpertAssignmentRepository
from app.repositories.rating_repository import RatingRepository
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
        self.rating_repo = RatingRepository(db)

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

    async def reopen(self, assignment_id: str, user_id: str) -> ExpertAssignment:
        """Membuka kembali assignment yang sudah selesai untuk diedit ulang.

        Mengubah status assignment dari ``completed`` menjadi ``in_progress``
        sehingga expert dapat merevisi penilaiannya.

        Args:
            assignment_id: ID assignment yang akan dibuka kembali.
            user_id: ID expert yang meminta reopen.

        Returns:
            Instance ExpertAssignment dengan status yang sudah diperbarui.

        Raises:
            HTTPException: Jika assignment tidak ditemukan (404), user bukan pemilik (403),
                           atau status bukan ``completed`` (400).
        """
        assignment = await self.get_by_id(assignment_id)

        if assignment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses ke assignment ini.",
            )

        if assignment.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=("Hanya assignment dengan status 'completed' yang dapat dibuka kembali."),
            )

        assignment.status = "in_progress"
        return await self.repo.update(assignment)

    async def delete(self, assignment_id: str) -> None:
        """Membatalkan penugasan expert.

        Args:
            assignment_id: ID assignment yang akan dihapus.

        Raises:
            HTTPException: Jika assignment tidak ditemukan (404).
        """
        assignment = await self.get_by_id(assignment_id)
        await self.repo.delete(assignment)

    async def archive_and_revise(
        self, assignment_id: str, archived_by: str
    ) -> tuple[ExpertAssignment, ExpertAssignment]:
        """Mengarsipkan assignment lama dan membuat assignment revisi baru.

        Assignment lama diubah statusnya menjadi ``archived`` sehingga tidak
        dihapus dan tetap tersimpan sebagai riwayat. Assignment baru dibuat
        dengan salinan semua penilaian dari assignment lama sehingga expert
        hanya perlu merevisi nilai yang keliru, bukan mengisi ulang dari nol.
        Kalkulasi CVI hanya menggunakan assignment non-archived.

        Args:
            assignment_id: ID assignment yang akan diarsipkan.
            archived_by: ID admin yang memicu pengarsipan.

        Returns:
            Tuple (archived_assignment, new_assignment).

        Raises:
            HTTPException: Jika assignment tidak ditemukan (404) atau sudah
                           berstatus archived (400).
        """
        assignment = await self.get_by_id(assignment_id)

        if assignment.status == "archived":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment sudah diarsipkan dan tidak dapat diarsipkan ulang.",
            )

        existing_ratings = await self.rating_repo.get_by_assignment(assignment_id)

        assignment.status = "archived"
        await self.repo.update(assignment)

        new_status = "in_progress" if existing_ratings else "pending"
        new_assignment = ExpertAssignment(
            id=str(uuid.uuid4()),
            instrument_id=assignment.instrument_id,
            user_id=assignment.user_id,
            assigned_by=archived_by,
            deadline=assignment.deadline,
            previous_assignment_id=assignment.id,
            revision_number=assignment.revision_number + 1,
            status=new_status,
        )
        created_assignment = await self.repo.create(new_assignment)

        for rating in existing_ratings:
            new_rating = Rating(
                id=str(uuid.uuid4()),
                assignment_id=created_assignment.id,
                item_id=rating.item_id,
                user_id=rating.user_id,
                relevance_score=rating.relevance_score,
                notes=rating.notes,
            )
            await self.rating_repo.create(new_rating)

        return assignment, created_assignment
