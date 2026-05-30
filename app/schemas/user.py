"""Schema Pydantic untuk entitas User."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Field dasar yang digunakan di beberapa schema User.

    Attributes:
        email: Alamat email pengguna.
        full_name: Nama lengkap pengguna.
        institution: Institusi/lembaga pengguna (opsional).
        expertise_area: Bidang keahlian pengguna (opsional).
    """

    email: EmailStr
    full_name: str
    institution: str | None = None
    expertise_area: str | None = None


class UserResponse(UserBase):
    """Schema response untuk data pengguna.

    Attributes:
        id: ID unik pengguna (sub dari Authentik).
        role: Role pengguna (admin/expert).
        is_active: Status aktif pengguna.
        created_at: Waktu pembuatan akun.
        updated_at: Waktu terakhir diperbarui.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "email": "dr.budi@universitas.ac.id",
                "full_name": "Dr. Budi Santoso",
                "institution": "Universitas Indonesia",
                "expertise_area": "Psikologi Pendidikan",
                "role": "expert",
                "is_active": True,
                "created_at": "2026-05-01T10:00:00",
                "updated_at": "2026-05-01T10:00:00",
            }
        },
    )

    id: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """Schema request untuk memperbarui profil pengguna.

    Hanya field yang dikirim yang akan diperbarui (partial update).

    Attributes:
        institution: Institusi baru (opsional).
        expertise_area: Bidang keahlian baru (opsional).
        is_active: Status aktif baru (opsional, admin only).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "institution": "Universitas Gadjah Mada",
                "expertise_area": "Pengukuran Pendidikan",
            }
        }
    )

    institution: str | None = None
    expertise_area: str | None = None
    is_active: bool | None = None
