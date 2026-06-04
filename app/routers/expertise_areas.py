"""Router untuk endpoint pengelolaan ExpertiseArea (bidang keahlian).

Daftar master bidang keahlian dapat dibaca oleh semua pengguna terautentikasi
(agar dapat dipilih sebagai keahlian), namun hanya admin yang dapat membuat,
mengubah, atau menghapusnya.
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.expertise_area import (
    ExpertiseAreaCreate,
    ExpertiseAreaResponse,
    ExpertiseAreaUpdate,
)
from app.services.expertise_area_service import ExpertiseAreaService
from app.utils.activity_logger import log_activity

router = APIRouter(prefix="/expertise-areas", tags=["Expertise Areas"])


@router.get(
    "/",
    response_model=list[ExpertiseAreaResponse],
    summary="Daftar bidang keahlian",
    description=(
        "Mengambil seluruh bidang keahlian pada daftar master. Dapat diakses "
        "oleh semua pengguna terautentikasi untuk dipilih sebagai keahlian."
    ),
    responses={401: {"description": "Token tidak valid."}},
)
async def list_expertise_areas(
    skip: int = 0,
    limit: int = 100,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ExpertiseAreaResponse]:
    """Mengambil daftar bidang keahlian.

    Args:
        skip: Jumlah record yang dilewati (pagination).
        limit: Jumlah maksimal record yang dikembalikan.
        _user: Pengguna terautentikasi (semua role).
        db: AsyncSession database.

    Returns:
        Daftar bidang keahlian.
    """
    service = ExpertiseAreaService(db)
    areas = await service.get_all(skip=skip, limit=limit)
    return [ExpertiseAreaResponse.model_validate(a) for a in areas]


@router.post(
    "/",
    response_model=ExpertiseAreaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat bidang keahlian",
    description="Membuat bidang keahlian baru pada daftar master. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak, diperlukan role admin."},
        409: {"description": "Nama bidang keahlian sudah ada."},
    },
)
async def create_expertise_area(
    data: ExpertiseAreaCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ExpertiseAreaResponse:
    """Membuat bidang keahlian baru (admin only).

    Args:
        data: Data bidang keahlian baru.
        request: HTTP request yang sedang diproses.
        admin: Admin yang membuat bidang keahlian.
        db: AsyncSession database.

    Returns:
        Bidang keahlian yang baru dibuat.
    """
    service = ExpertiseAreaService(db)
    area = await service.create(data)
    await log_activity(
        db=db,
        action="create_expertise_area",
        request=request,
        user_id=admin.id,
        resource_type="expertise_area",
        resource_id=area.id,
    )
    return ExpertiseAreaResponse.model_validate(area)


@router.patch(
    "/{expertise_area_id}",
    response_model=ExpertiseAreaResponse,
    summary="Perbarui bidang keahlian",
    description="Memperbarui nama atau deskripsi bidang keahlian. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak, diperlukan role admin."},
        404: {"description": "Bidang keahlian tidak ditemukan."},
        409: {"description": "Nama bidang keahlian sudah ada."},
    },
)
async def update_expertise_area(
    expertise_area_id: str,
    data: ExpertiseAreaUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ExpertiseAreaResponse:
    """Memperbarui bidang keahlian (admin only).

    Args:
        expertise_area_id: ID bidang keahlian yang akan diperbarui.
        data: Data pembaruan bidang keahlian.
        request: HTTP request yang sedang diproses.
        admin: Admin yang melakukan pembaruan.
        db: AsyncSession database.

    Returns:
        Bidang keahlian yang sudah diperbarui.
    """
    service = ExpertiseAreaService(db)
    area = await service.update(expertise_area_id, data)
    await log_activity(
        db=db,
        action="update_expertise_area",
        request=request,
        user_id=admin.id,
        resource_type="expertise_area",
        resource_id=expertise_area_id,
    )
    return ExpertiseAreaResponse.model_validate(area)


@router.delete(
    "/{expertise_area_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Hapus bidang keahlian",
    description=(
        "Menghapus bidang keahlian dari daftar master. Keterkaitan dengan "
        "pengguna akan otomatis dilepaskan. Hanya admin."
    ),
    responses={
        403: {"description": "Akses ditolak, diperlukan role admin."},
        404: {"description": "Bidang keahlian tidak ditemukan."},
    },
)
async def delete_expertise_area(
    expertise_area_id: str,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Menghapus bidang keahlian (admin only).

    Args:
        expertise_area_id: ID bidang keahlian yang akan dihapus.
        request: HTTP request yang sedang diproses.
        admin: Admin yang melakukan aksi.
        db: AsyncSession database.

    Returns:
        Pesan konfirmasi.
    """
    service = ExpertiseAreaService(db)
    await service.delete(expertise_area_id)
    await log_activity(
        db=db,
        action="delete_expertise_area",
        request=request,
        user_id=admin.id,
        resource_type="expertise_area",
        resource_id=expertise_area_id,
    )
    return MessageResponse(message=f"Bidang keahlian '{expertise_area_id}' berhasil dihapus.")
