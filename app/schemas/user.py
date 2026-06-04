"""Schema Pydantic untuk entitas User."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.expertise_area import ExpertiseAreaResponse


class UserBase(BaseModel):
    """Field dasar yang digunakan di beberapa schema User.

    Attributes:
        email: Alamat email pengguna.
        full_name: Nama lengkap pengguna.
        institution: Institusi/lembaga pengguna (opsional).
    """

    email: EmailStr
    full_name: str
    institution: str | None = None


class UserResponse(UserBase):
    """Schema response untuk data pengguna.

    Attributes:
        id: ID unik pengguna (sub dari Authentik).
        email: Alamat email pengguna (dioverride ke str untuk mendukung TLD
            yang direservasi seperti .test di lingkungan pengujian).
        role: Role pengguna (admin/expert).
        is_active: Status aktif pengguna.
        expertise_areas: Daftar bidang keahlian yang dimiliki pengguna.
        created_at: Waktu pembuatan akun.
        updated_at: Waktu terakhir diperbarui.
    """

    # Override EmailStr → str agar validasi format tidak dilakukan pada response.
    # EmailStr pada UserBase tetap memvalidasi input saat create/update.
    email: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "email": "dr.budi@universitas.ac.id",
                "full_name": "Dr. Budi Santoso",
                "institution": "Universitas Indonesia",
                "expertise_areas": [
                    {
                        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                        "name": "Psikologi Pendidikan",
                        "description": "Bidang yang menelaah proses belajar.",
                        "created_at": "2026-05-01T10:00:00",
                        "updated_at": "2026-05-01T10:00:00",
                    }
                ],
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
    expertise_areas: list[ExpertiseAreaResponse] = []
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """Schema request untuk memperbarui profil pengguna (admin only).

    Hanya field yang dikirim yang akan diperbarui (partial update).

    Attributes:
        institution: Institusi baru (opsional).
        expertise_area_ids: Daftar ID bidang keahlian untuk ditetapkan ke
            pengguna (opsional). Jika dikirim, akan menggantikan seluruh
            keahlian pengguna dengan daftar ini.
        is_active: Status aktif baru (opsional, admin only).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "institution": "Universitas Gadjah Mada",
                "expertise_area_ids": ["b2c3d4e5-f6a7-8901-bcde-f12345678901"],
            }
        }
    )

    institution: str | None = None
    expertise_area_ids: list[str] | None = None
    is_active: bool | None = None


class UserSelfUpdate(BaseModel):
    """Schema request bagi pengguna untuk memperbarui identitas pribadinya.

    Digunakan pada endpoint `PATCH /users/me`. Berbeda dengan `UserUpdate`,
    schema ini mengizinkan pengguna mengubah `full_name`-nya sendiri, namun
    tidak mengizinkan perubahan `is_active` (khusus admin). Hanya field yang
    dikirim yang akan diperbarui (partial update).

    Attributes:
        full_name: Nama lengkap baru (opsional, tidak boleh string kosong).
        institution: Institusi baru (opsional).
        expertise_area_ids: Daftar ID bidang keahlian milik pengguna (opsional).
            Jika dikirim, akan menggantikan seluruh keahlian pengguna.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Dr. Budi Santoso, M.Psi.",
                "institution": "Universitas Gadjah Mada",
                "expertise_area_ids": ["b2c3d4e5-f6a7-8901-bcde-f12345678901"],
            }
        }
    )

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    institution: str | None = None
    expertise_area_ids: list[str] | None = None
