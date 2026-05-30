"""Router untuk endpoint autentikasi."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse
from app.utils.activity_logger import log_activity

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/sync",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Sinkronisasi user dari Authentik",
    description=(
        "Menerima JWT Bearer token dari Authentik, menyinkronkan data pengguna "
        "(email, nama, role dari groups) ke database lokal, dan mengembalikan "
        "profil pengguna yang sudah disinkronisasi. "
        "Endpoint ini dipanggil setelah login berhasil di Authentik."
    ),
    responses={
        401: {"description": "Token tidak valid atau kedaluwarsa."},
        403: {"description": "Akun pengguna tidak aktif."},
        503: {"description": "Identity provider tidak dapat dihubungi."},
    },
)
async def sync_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Sinkronisasi data pengguna dari JWT Authentik ke database lokal.

    Args:
        request: HTTP request yang sedang diproses.
        current_user: User yang terautentikasi dari JWT.
        db: AsyncSession database.

    Returns:
        Profil pengguna yang sudah disinkronisasi.
    """
    await log_activity(
        db=db,
        action="login",
        request=request,
        user_id=current_user.id,
        resource_type="user",
        resource_id=current_user.id,
    )
    return UserResponse.model_validate(current_user)
