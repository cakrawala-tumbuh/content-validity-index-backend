"""Schema Pydantic untuk entitas ExpertiseArea (bidang keahlian)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExpertiseAreaBase(BaseModel):
    """Field dasar bidang keahlian.

    Attributes:
        name: Nama bidang keahlian (unik).
        description: Deskripsi singkat (opsional).
    """

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ExpertiseAreaCreate(ExpertiseAreaBase):
    """Schema request untuk membuat bidang keahlian baru (admin only)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Psikologi Pendidikan",
                "description": "Bidang yang menelaah proses belajar dan pengajaran.",
            }
        }
    )


class ExpertiseAreaUpdate(BaseModel):
    """Schema request untuk memperbarui bidang keahlian (admin only).

    Hanya field yang dikirim yang akan diperbarui (partial update).

    Attributes:
        name: Nama baru bidang keahlian (opsional).
        description: Deskripsi baru (opsional).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Pengukuran Pendidikan",
                "description": "Fokus pada pengembangan dan validasi instrumen.",
            }
        }
    )

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ExpertiseAreaResponse(ExpertiseAreaBase):
    """Schema response untuk data bidang keahlian.

    Attributes:
        id: ID unik bidang keahlian.
        name: Nama bidang keahlian.
        description: Deskripsi singkat.
        created_at: Waktu pembuatan.
        updated_at: Waktu terakhir diperbarui.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "name": "Psikologi Pendidikan",
                "description": "Bidang yang menelaah proses belajar dan pengajaran.",
                "created_at": "2026-06-04T10:00:00",
                "updated_at": "2026-06-04T10:00:00",
            }
        },
    )

    id: str
    created_at: datetime
    updated_at: datetime
