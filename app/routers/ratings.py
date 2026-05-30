"""Router untuk endpoint pengelolaan penilaian (Rating) dan assignment expert."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_expert
from app.models.user import User
from app.schemas.expert_assignment import AssignmentResponse
from app.schemas.rating import RatingBulkCreate, RatingResponse, RatingUpdate
from app.services.expert_assignment_service import ExpertAssignmentService
from app.services.rating_service import RatingService
from app.utils.activity_logger import log_activity

router = APIRouter(tags=["Ratings"])


@router.get(
    "/my-assignments",
    response_model=list[AssignmentResponse],
    summary="Assignment saya",
    description="Mengambil semua instrumen yang di-assign ke pengguna yang sedang login.",
    responses={401: {"description": "Token tidak valid."}},
)
async def get_my_assignments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AssignmentResponse]:
    """Mengambil daftar assignment milik pengguna yang sedang login.

    Args:
        current_user: Pengguna yang sedang login.
        db: AsyncSession database.

    Returns:
        Daftar assignment expert.
    """
    service = ExpertAssignmentService(db)
    assignments = await service.get_my_assignments(current_user.id)
    return [AssignmentResponse.model_validate(a) for a in assignments]


@router.get(
    "/assignments/{assignment_id}/ratings",
    response_model=list[RatingResponse],
    summary="Daftar penilaian dalam assignment",
    description=(
        "Mengambil semua rating yang sudah diberikan dalam sebuah assignment. "
        "Expert hanya dapat melihat rating miliknya sendiri."
    ),
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Assignment tidak ditemukan."},
    },
)
async def get_ratings(
    assignment_id: str,
    current_user: User = Depends(require_expert),
    db: AsyncSession = Depends(get_db),
) -> list[RatingResponse]:
    """Mengambil daftar rating dalam sebuah assignment.

    Args:
        assignment_id: ID assignment.
        current_user: Pengguna yang sedang login.
        db: AsyncSession database.

    Returns:
        Daftar rating.
    """
    service = RatingService(db)
    ratings = await service.get_by_assignment(
        assignment_id=assignment_id,
        user_id=current_user.id,
        role=current_user.role,
    )
    return [RatingResponse.model_validate(r) for r in ratings]


@router.post(
    "/assignments/{assignment_id}/ratings/bulk",
    response_model=list[RatingResponse],
    status_code=status.HTTP_200_OK,
    summary="Submit penilaian massal",
    description=(
        "Mengirimkan penilaian untuk semua item dalam satu assignment sekaligus. "
        "Jika rating untuk item tertentu sudah ada, akan di-update (upsert). "
        "Hanya expert yang di-assign yang dapat submit."
    ),
    responses={
        403: {"description": "Akses ditolak atau bukan expert yang di-assign."},
        404: {"description": "Assignment tidak ditemukan."},
        422: {"description": "Skor relevansi harus antara 1 dan 4."},
    },
)
async def bulk_submit_ratings(
    assignment_id: str,
    data: RatingBulkCreate,
    request: Request,
    current_user: User = Depends(require_expert),
    db: AsyncSession = Depends(get_db),
) -> list[RatingResponse]:
    """Submit penilaian massal untuk semua item dalam assignment.

    Args:
        assignment_id: ID assignment yang dinilai.
        data: Data penilaian berisi daftar item dan skor relevansi.
        request: HTTP request.
        current_user: Expert yang menilai.
        db: AsyncSession database.

    Returns:
        Daftar rating yang berhasil disimpan.
    """
    service = RatingService(db)
    ratings = await service.bulk_submit(
        assignment_id=assignment_id,
        data=data,
        user_id=current_user.id,
    )
    await log_activity(
        db=db,
        action="bulk_submit_ratings",
        request=request,
        user_id=current_user.id,
        resource_type="expert_assignment",
        resource_id=assignment_id,
        metadata={"count": len(ratings)},
    )
    return [RatingResponse.model_validate(r) for r in ratings]


@router.patch(
    "/assignments/{assignment_id}/ratings/{rating_id}",
    response_model=RatingResponse,
    summary="Perbarui satu penilaian",
    description=(
        "Memperbarui skor atau catatan untuk satu penilaian item. "
        "Hanya expert pemilik rating yang dapat memperbarui."
    ),
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Rating atau assignment tidak ditemukan."},
    },
)
async def update_rating(
    assignment_id: str,
    rating_id: str,
    data: RatingUpdate,
    request: Request,
    current_user: User = Depends(require_expert),
    db: AsyncSession = Depends(get_db),
) -> RatingResponse:
    """Memperbarui satu penilaian item.

    Args:
        assignment_id: ID assignment (untuk validasi kepemilikan).
        rating_id: ID rating yang akan diperbarui.
        data: Data pembaruan (skor atau catatan).
        request: HTTP request.
        current_user: Expert yang melakukan pembaruan.
        db: AsyncSession database.

    Returns:
        Rating yang sudah diperbarui.
    """
    service = RatingService(db)
    updated = await service.update_single(
        rating_id=rating_id,
        assignment_id=assignment_id,
        data=data,
        user_id=current_user.id,
        role=current_user.role,
    )
    await log_activity(
        db=db,
        action="update_rating",
        request=request,
        user_id=current_user.id,
        resource_type="rating",
        resource_id=rating_id,
    )
    return RatingResponse.model_validate(updated)
