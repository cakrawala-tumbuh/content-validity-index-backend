"""Router untuk endpoint pengelolaan User."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService
from app.utils.activity_logger import log_activity

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Profil pengguna saat ini",
    description="Mengembalikan profil lengkap pengguna yang sedang login.",
    responses={
        401: {"description": "Token tidak valid."},
        403: {"description": "Akun tidak aktif."},
    },
)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Mengambil profil pengguna yang sedang login.

    Args:
        current_user: User yang terautentikasi.

    Returns:
        Profil pengguna saat ini.
    """
    return UserResponse.model_validate(current_user)


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="Daftar semua pengguna",
    description="Mengambil semua pengguna terdaftar. Hanya dapat diakses oleh admin.",
    responses={403: {"description": "Akses ditolak, diperlukan role admin."}},
)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserResponse]:
    """Mengambil daftar semua pengguna (admin only).

    Args:
        skip: Jumlah record yang dilewati (pagination).
        limit: Jumlah maksimal record yang dikembalikan.
        _admin: Dependency yang memvalidasi role admin.
        db: AsyncSession database.

    Returns:
        Daftar profil pengguna.
    """
    service = UserService(db)
    users = await service.get_all(skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Detail pengguna",
    description="Mengambil detail profil pengguna berdasarkan ID. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak, diperlukan role admin."},
        404: {"description": "Pengguna tidak ditemukan."},
    },
)
async def get_user(
    user_id: str,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Mengambil detail pengguna berdasarkan ID (admin only).

    Args:
        user_id: ID unik pengguna.
        _admin: Dependency yang memvalidasi role admin.
        db: AsyncSession database.

    Returns:
        Profil pengguna.
    """
    service = UserService(db)
    user = await service.get_by_id(user_id)
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Perbarui profil pengguna",
    description=(
        "Memperbarui profil pengguna berdasarkan ID. Admin dapat memperbarui "
        "semua field termasuk `is_active`."
    ),
    responses={
        403: {"description": "Akses ditolak, diperlukan role admin."},
        404: {"description": "Pengguna tidak ditemukan."},
    },
)
async def update_user(
    user_id: str,
    data: UserUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Memperbarui profil pengguna (admin only).

    Args:
        user_id: ID unik pengguna yang akan diperbarui.
        data: Data pembaruan.
        request: HTTP request yang sedang diproses.
        admin: Admin yang melakukan pembaruan.
        db: AsyncSession database.

    Returns:
        Profil pengguna yang sudah diperbarui.
    """
    service = UserService(db)
    updated = await service.update(user_id, data)
    await log_activity(
        db=db,
        action="update_user",
        request=request,
        user_id=admin.id,
        resource_type="user",
        resource_id=user_id,
    )
    return UserResponse.model_validate(updated)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Nonaktifkan pengguna",
    description="Menonaktifkan akun pengguna (soft delete via is_active=False). Hanya admin.",
    responses={
        403: {"description": "Akses ditolak, diperlukan role admin."},
        404: {"description": "Pengguna tidak ditemukan."},
    },
)
async def deactivate_user(
    user_id: str,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Menonaktifkan akun pengguna (admin only).

    Args:
        user_id: ID unik pengguna yang akan dinonaktifkan.
        request: HTTP request yang sedang diproses.
        admin: Admin yang melakukan aksi.
        db: AsyncSession database.

    Returns:
        Pesan konfirmasi.
    """
    service = UserService(db)
    data = UserUpdate(is_active=False)
    await service.update(user_id, data)
    await log_activity(
        db=db,
        action="deactivate_user",
        request=request,
        user_id=admin.id,
        resource_type="user",
        resource_id=user_id,
    )
    return MessageResponse(message=f"Pengguna '{user_id}' berhasil dinonaktifkan.")
