"""Router untuk endpoint pengelolaan Instrumen, Item, Assignment, dan CVI."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.cvi import CVIResult, InstrumentExpertRatingsResponse
from app.schemas.domain import DomainCreate, DomainResponse, DomainUpdate
from app.schemas.expert_assignment import AssignmentCreate, AssignmentResponse
from app.schemas.instrument import InstrumentCreate, InstrumentResponse, InstrumentUpdate
from app.schemas.item import ItemBulkCreate, ItemCreate, ItemResponse, ItemUpdate
from app.services.cvi_service import CVIService
from app.services.rating_service import RatingService
from app.services.domain_service import DomainService
from app.services.expert_assignment_service import ExpertAssignmentService
from app.services.instrument_service import InstrumentService
from app.services.item_service import ItemService
from app.utils.activity_logger import log_activity
from app.utils.excel_exporter import generate_cvi_excel

router = APIRouter(prefix="/instruments", tags=["Instruments"])


# ────────────────────────────────────────────────────────────
#  Instruments
# ────────────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=list[InstrumentResponse],
    summary="Daftar instrumen",
    description=(
        "Admin: semua instrumen. Expert: hanya instrumen yang sudah di-assign ke user tersebut."
    ),
    responses={401: {"description": "Token tidak valid."}},
)
async def list_instruments(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InstrumentResponse]:
    """Mengambil daftar instrumen sesuai role pengguna.

    Args:
        skip: Jumlah record yang dilewati (pagination).
        limit: Jumlah maksimal record yang dikembalikan.
        current_user: Pengguna yang sedang login.
        db: AsyncSession database.

    Returns:
        Daftar instrumen.
    """
    service = InstrumentService(db)
    instruments = await service.get_all(
        user_id=current_user.id, role=current_user.role, skip=skip, limit=limit
    )
    return [InstrumentResponse.model_validate(i) for i in instruments]


@router.post(
    "/",
    response_model=InstrumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat instrumen baru",
    description="Membuat instrumen CVI baru. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak, diperlukan role admin."},
    },
)
async def create_instrument(
    data: InstrumentCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> InstrumentResponse:
    """Membuat instrumen baru (admin only).

    Args:
        data: Data instrumen baru.
        request: HTTP request yang sedang diproses.
        admin: Admin yang membuat instrumen.
        db: AsyncSession database.

    Returns:
        Instrumen yang baru dibuat.
    """
    service = InstrumentService(db)
    instrument = await service.create(data, created_by=admin.id)
    await log_activity(
        db=db,
        action="create_instrument",
        request=request,
        user_id=admin.id,
        resource_type="instrument",
        resource_id=instrument.id,
    )
    # Commit sebelum mengembalikan response agar instrumen sudah tersimpan di DB
    # saat klien langsung mengirim request lanjutan (misalnya bulk create items).
    # FastAPI menjalankan cleanup yield dependency SETELAH response dikirim,
    # sehingga tanpa commit eksplisit di sini, ada race condition.
    await db.commit()
    return InstrumentResponse.model_validate(instrument)


@router.get(
    "/{instrument_id}",
    response_model=InstrumentResponse,
    summary="Detail instrumen",
    description="Mengambil detail instrumen berdasarkan ID.",
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Instrumen tidak ditemukan."},
    },
)
async def get_instrument(
    instrument_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstrumentResponse:
    """Mengambil detail satu instrumen.

    Args:
        instrument_id: ID instrumen.
        current_user: Pengguna yang sedang login.
        db: AsyncSession database.

    Returns:
        Detail instrumen.
    """
    service = InstrumentService(db)
    instrument = await service.get_by_id(instrument_id)
    return InstrumentResponse.model_validate(instrument)


@router.patch(
    "/{instrument_id}",
    response_model=InstrumentResponse,
    summary="Perbarui instrumen",
    description="Memperbarui nama, deskripsi, versi, atau status instrumen. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak, diperlukan role admin."},
        404: {"description": "Instrumen tidak ditemukan."},
    },
)
async def update_instrument(
    instrument_id: str,
    data: InstrumentUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> InstrumentResponse:
    """Memperbarui instrumen (admin only).

    Args:
        instrument_id: ID instrumen yang akan diperbarui.
        data: Data pembaruan.
        request: HTTP request.
        admin: Admin yang melakukan pembaruan.
        db: AsyncSession database.

    Returns:
        Instrumen yang sudah diperbarui.
    """
    service = InstrumentService(db)
    updated = await service.update(instrument_id, data)
    await log_activity(
        db=db,
        action="update_instrument",
        request=request,
        user_id=admin.id,
        resource_type="instrument",
        resource_id=instrument_id,
    )
    return InstrumentResponse.model_validate(updated)


@router.delete(
    "/{instrument_id}",
    response_model=MessageResponse,
    summary="Hapus instrumen",
    description="Menghapus instrumen beserta seluruh item dan assignment-nya. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak, diperlukan role admin."},
        404: {"description": "Instrumen tidak ditemukan."},
    },
)
async def delete_instrument(
    instrument_id: str,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Menghapus instrumen (admin only).

    Args:
        instrument_id: ID instrumen yang akan dihapus.
        request: HTTP request.
        admin: Admin yang menghapus.
        db: AsyncSession database.

    Returns:
        Pesan konfirmasi.
    """
    service = InstrumentService(db)
    await service.delete(instrument_id)
    await log_activity(
        db=db,
        action="delete_instrument",
        request=request,
        user_id=admin.id,
        resource_type="instrument",
        resource_id=instrument_id,
    )
    return MessageResponse(message=f"Instrumen '{instrument_id}' berhasil dihapus.")


# ────────────────────────────────────────────────────────────
#  Items
# ────────────────────────────────────────────────────────────


@router.get(
    "/{instrument_id}/items",
    response_model=list[ItemResponse],
    summary="Daftar item instrumen",
    description="Mengambil semua item dari sebuah instrumen.",
    responses={
        401: {"description": "Token tidak valid."},
        404: {"description": "Instrumen tidak ditemukan."},
    },
)
async def list_items(
    instrument_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ItemResponse]:
    """Mengambil daftar item dalam sebuah instrumen.

    Args:
        instrument_id: ID instrumen.
        current_user: Pengguna yang sedang login.
        db: AsyncSession database.

    Returns:
        Daftar item terurut berdasarkan sequence_number.
    """
    service = ItemService(db)
    items = await service.get_by_instrument(instrument_id)
    return [ItemResponse.model_validate(i) for i in items]


@router.post(
    "/{instrument_id}/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tambah satu item",
    description="Menambahkan satu item ke instrumen. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Instrumen tidak ditemukan."},
    },
)
async def create_item(
    instrument_id: str,
    data: ItemCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse:
    """Menambahkan satu item ke instrumen (admin only).

    Args:
        instrument_id: ID instrumen.
        data: Data item baru.
        request: HTTP request.
        admin: Admin yang menambahkan item.
        db: AsyncSession database.

    Returns:
        Item yang baru dibuat.
    """
    service = ItemService(db)
    item = await service.create(instrument_id, data)
    await log_activity(
        db=db,
        action="create_item",
        request=request,
        user_id=admin.id,
        resource_type="item",
        resource_id=item.id,
    )
    return ItemResponse.model_validate(item)


@router.post(
    "/{instrument_id}/items/bulk",
    response_model=list[ItemResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tambah banyak item sekaligus",
    description="Menambahkan beberapa item ke instrumen dalam satu request. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Instrumen tidak ditemukan."},
    },
)
async def bulk_create_items(
    instrument_id: str,
    data: ItemBulkCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ItemResponse]:
    """Menambahkan banyak item ke instrumen sekaligus (admin only).

    Args:
        instrument_id: ID instrumen.
        data: Data item dalam bentuk list.
        request: HTTP request.
        admin: Admin yang menambahkan item.
        db: AsyncSession database.

    Returns:
        Daftar item yang baru dibuat.
    """
    service = ItemService(db)
    items = await service.bulk_create(instrument_id, data)
    await log_activity(
        db=db,
        action="bulk_create_items",
        request=request,
        user_id=admin.id,
        resource_type="instrument",
        resource_id=instrument_id,
        metadata={"count": len(items)},
    )
    return [ItemResponse.model_validate(i) for i in items]


@router.patch(
    "/{instrument_id}/items/{item_id}",
    response_model=ItemResponse,
    summary="Perbarui item",
    description="Memperbarui konten atau metadata sebuah item. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Item atau instrumen tidak ditemukan."},
    },
)
async def update_item(
    instrument_id: str,
    item_id: str,
    data: ItemUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse:
    """Memperbarui item dalam instrumen (admin only).

    Args:
        instrument_id: ID instrumen.
        item_id: ID item yang akan diperbarui.
        data: Data pembaruan item.
        request: HTTP request.
        admin: Admin yang memperbarui.
        db: AsyncSession database.

    Returns:
        Item yang sudah diperbarui.
    """
    service = ItemService(db)
    updated = await service.update(item_id, instrument_id, data)
    await log_activity(
        db=db,
        action="update_item",
        request=request,
        user_id=admin.id,
        resource_type="item",
        resource_id=item_id,
    )
    return ItemResponse.model_validate(updated)


@router.delete(
    "/{instrument_id}/items/{item_id}",
    response_model=MessageResponse,
    summary="Hapus item",
    description="Menghapus sebuah item dari instrumen. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Item atau instrumen tidak ditemukan."},
    },
)
async def delete_item(
    instrument_id: str,
    item_id: str,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Menghapus item dari instrumen (admin only).

    Args:
        instrument_id: ID instrumen.
        item_id: ID item yang akan dihapus.
        request: HTTP request.
        admin: Admin yang menghapus.
        db: AsyncSession database.

    Returns:
        Pesan konfirmasi.
    """
    service = ItemService(db)
    await service.delete(item_id, instrument_id)
    await log_activity(
        db=db,
        action="delete_item",
        request=request,
        user_id=admin.id,
        resource_type="item",
        resource_id=item_id,
    )
    return MessageResponse(message=f"Item '{item_id}' berhasil dihapus.")


# ────────────────────────────────────────────────────────────
#  Domains
# ────────────────────────────────────────────────────────────


@router.get(
    "/{instrument_id}/domains",
    response_model=list[DomainResponse],
    summary="Daftar domain instrumen",
    description="Mengambil semua domain/dimensi yang didefinisikan dalam instrumen.",
    responses={
        401: {"description": "Token tidak valid."},
        404: {"description": "Instrumen tidak ditemukan."},
    },
)
async def list_domains(
    instrument_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DomainResponse]:
    """Mengambil daftar domain dalam sebuah instrumen.

    Args:
        instrument_id: ID instrumen.
        current_user: Pengguna yang sedang login.
        db: AsyncSession database.

    Returns:
        Daftar domain dalam instrumen.
    """
    service = DomainService(db)
    domains = await service.get_by_instrument(instrument_id)
    return [DomainResponse.model_validate(d) for d in domains]


@router.post(
    "/{instrument_id}/domains",
    response_model=DomainResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tambah domain",
    description="Menambahkan domain/dimensi baru ke instrumen. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Instrumen tidak ditemukan."},
    },
)
async def create_domain(
    instrument_id: str,
    data: DomainCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> DomainResponse:
    """Menambahkan domain baru ke instrumen (admin only).

    Args:
        instrument_id: ID instrumen.
        data: Data domain baru.
        request: HTTP request.
        admin: Admin yang menambahkan domain.
        db: AsyncSession database.

    Returns:
        Domain yang baru dibuat.
    """
    service = DomainService(db)
    domain = await service.create(instrument_id, data)
    await log_activity(
        db=db,
        action="create_domain",
        request=request,
        user_id=admin.id,
        resource_type="domain",
        resource_id=domain.id,
    )
    return DomainResponse.model_validate(domain)


@router.patch(
    "/{instrument_id}/domains/{domain_id}",
    response_model=DomainResponse,
    summary="Perbarui domain",
    description="Memperbarui nama domain/dimensi. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Domain atau instrumen tidak ditemukan."},
    },
)
async def update_domain(
    instrument_id: str,
    domain_id: str,
    data: DomainUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> DomainResponse:
    """Memperbarui domain dalam instrumen (admin only).

    Args:
        instrument_id: ID instrumen.
        domain_id: ID domain yang akan diperbarui.
        data: Data pembaruan domain.
        request: HTTP request.
        admin: Admin yang memperbarui.
        db: AsyncSession database.

    Returns:
        Domain yang sudah diperbarui.
    """
    service = DomainService(db)
    updated = await service.update(domain_id, instrument_id, data)
    await log_activity(
        db=db,
        action="update_domain",
        request=request,
        user_id=admin.id,
        resource_type="domain",
        resource_id=domain_id,
    )
    return DomainResponse.model_validate(updated)


@router.delete(
    "/{instrument_id}/domains/{domain_id}",
    response_model=MessageResponse,
    summary="Hapus domain",
    description=(
        "Menghapus domain dari instrumen. "
        "Item yang terkait akan kehilangan referensi domain. Hanya admin."
    ),
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Domain atau instrumen tidak ditemukan."},
    },
)
async def delete_domain(
    instrument_id: str,
    domain_id: str,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Menghapus domain dari instrumen (admin only).

    Args:
        instrument_id: ID instrumen.
        domain_id: ID domain yang akan dihapus.
        request: HTTP request.
        admin: Admin yang menghapus.
        db: AsyncSession database.

    Returns:
        Pesan konfirmasi.
    """
    service = DomainService(db)
    await service.delete(domain_id, instrument_id)
    await log_activity(
        db=db,
        action="delete_domain",
        request=request,
        user_id=admin.id,
        resource_type="domain",
        resource_id=domain_id,
    )
    return MessageResponse(message=f"Domain '{domain_id}' berhasil dihapus.")


# ────────────────────────────────────────────────────────────
#  Expert Assignments
# ────────────────────────────────────────────────────────────


@router.get(
    "/{instrument_id}/assignments",
    response_model=list[AssignmentResponse],
    summary="Daftar assignment expert",
    description="Mengambil daftar expert yang di-assign ke instrumen ini. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Instrumen tidak ditemukan."},
    },
)
async def list_assignments(
    instrument_id: str,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AssignmentResponse]:
    """Mengambil daftar assignment expert pada instrumen (admin only).

    Args:
        instrument_id: ID instrumen.
        _admin: Dependency yang memvalidasi role admin.
        db: AsyncSession database.

    Returns:
        Daftar assignment expert.
    """
    service = ExpertAssignmentService(db)
    assignments = await service.get_by_instrument(instrument_id)
    return [AssignmentResponse.model_validate(a) for a in assignments]


@router.post(
    "/{instrument_id}/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign expert ke instrumen",
    description="Menugaskan seorang expert untuk menilai instrumen. Hanya admin.",
    responses={
        400: {"description": "Expert sudah di-assign sebelumnya."},
        403: {"description": "Akses ditolak atau target bukan expert."},
        404: {"description": "Instrumen atau user tidak ditemukan."},
    },
)
async def create_assignment(
    instrument_id: str,
    data: AssignmentCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AssignmentResponse:
    """Menugaskan expert untuk menilai instrumen (admin only).

    Args:
        instrument_id: ID instrumen.
        data: Data assignment (user_id expert, deadline).
        request: HTTP request.
        admin: Admin yang melakukan assignment.
        db: AsyncSession database.

    Returns:
        Data assignment yang baru dibuat.
    """
    service = ExpertAssignmentService(db)
    assignment = await service.create(instrument_id, data, assigned_by=admin.id)
    await log_activity(
        db=db,
        action="assign_expert",
        request=request,
        user_id=admin.id,
        resource_type="expert_assignment",
        resource_id=assignment.id,
        metadata={"expert_id": data.user_id},
    )
    return AssignmentResponse.model_validate(assignment)


@router.delete(
    "/{instrument_id}/assignments/{assignment_id}",
    response_model=MessageResponse,
    summary="Batalkan assignment",
    description="Menghapus assignment expert dari instrumen. Hanya admin.",
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Assignment tidak ditemukan."},
    },
)
async def delete_assignment(
    instrument_id: str,
    assignment_id: str,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Menghapus assignment expert (admin only).

    Args:
        instrument_id: ID instrumen (untuk konteks).
        assignment_id: ID assignment yang akan dihapus.
        request: HTTP request.
        admin: Admin yang menghapus.
        db: AsyncSession database.

    Returns:
        Pesan konfirmasi.
    """
    service = ExpertAssignmentService(db)
    await service.delete(assignment_id)
    await log_activity(
        db=db,
        action="delete_assignment",
        request=request,
        user_id=admin.id,
        resource_type="expert_assignment",
        resource_id=assignment_id,
    )
    return MessageResponse(message=f"Assignment '{assignment_id}' berhasil dihapus.")


# ────────────────────────────────────────────────────────────
#  Expert Ratings (admin view)
# ────────────────────────────────────────────────────────────


@router.get(
    "/{instrument_id}/expert-ratings",
    response_model=InstrumentExpertRatingsResponse,
    summary="Penilaian per expert",
    description=(
        "Mengambil penilaian setiap expert per item untuk sebuah instrumen. "
        "Menampilkan skor, catatan, dan status penilaian masing-masing expert. "
        "Item yang belum dinilai ditampilkan dengan skor None. Hanya admin."
    ),
    responses={
        403: {"description": "Akses ditolak."},
        404: {"description": "Instrumen tidak ditemukan."},
    },
)
async def get_expert_ratings(
    instrument_id: str,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> InstrumentExpertRatingsResponse:
    """Mengambil penilaian semua expert per item (admin only).

    Args:
        instrument_id: ID instrumen.
        _admin: Dependency yang memvalidasi role admin.
        db: AsyncSession database.

    Returns:
        Penilaian per expert lengkap dengan skor per item.
    """
    service = RatingService(db)
    return await service.get_expert_ratings_for_instrument(instrument_id)


# ────────────────────────────────────────────────────────────
#  CVI Calculation & Export
# ────────────────────────────────────────────────────────────


@router.get(
    "/{instrument_id}/cvi",
    response_model=CVIResult,
    summary="Hasil kalkulasi CVI",
    description=(
        "Menghitung dan mengembalikan hasil Content Validity Index (I-CVI per item, "
        "S-CVI/Ave, S-CVI/UA) berdasarkan semua penilaian yang masuk. Hanya admin."
    ),
    responses={
        400: {"description": "Belum ada penilaian atau instrumen tidak memiliki item."},
        403: {"description": "Akses ditolak."},
        404: {"description": "Instrumen tidak ditemukan."},
    },
)
async def calculate_cvi(
    instrument_id: str,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> CVIResult:
    """Menghitung hasil CVI untuk instrumen (admin only).

    Args:
        instrument_id: ID instrumen.
        _admin: Dependency yang memvalidasi role admin.
        db: AsyncSession database.

    Returns:
        Hasil CVI lengkap (I-CVI per item, S-CVI/Ave, S-CVI/UA).
    """
    service = CVIService(db)
    return await service.calculate(instrument_id)


@router.get(
    "/{instrument_id}/cvi/export",
    summary="Ekspor hasil CVI ke Excel",
    description=("Mengunduh hasil kalkulasi CVI dalam format file Excel (.xlsx). Hanya admin."),
    responses={
        200: {"content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}},
        400: {"description": "Belum ada penilaian."},
        403: {"description": "Akses ditolak."},
        404: {"description": "Instrumen tidak ditemukan."},
    },
)
async def export_cvi_excel(
    instrument_id: str,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Mengekspor hasil CVI instrumen ke file Excel (admin only).

    Args:
        instrument_id: ID instrumen.
        request: HTTP request.
        admin: Admin yang mengekspor.
        db: AsyncSession database.

    Returns:
        File Excel (.xlsx) berisi hasil CVI.
    """
    cvi_service = CVIService(db)
    result = await cvi_service.calculate(instrument_id)
    excel_bytes = generate_cvi_excel(result)
    await log_activity(
        db=db,
        action="export_cvi_excel",
        request=request,
        user_id=admin.id,
        resource_type="instrument",
        resource_id=instrument_id,
    )
    filename = f"CVI_{result.instrument_name.replace(' ', '_')}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
