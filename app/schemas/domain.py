"""Schema Pydantic untuk entitas Domain."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DomainCreate(BaseModel):
    """Schema request untuk membuat domain baru dalam sebuah instrumen.

    Attributes:
        name: Nama domain/dimensi.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Literasi Kesehatan",
            }
        }
    )

    name: str = Field(min_length=1, max_length=255)


class DomainUpdate(BaseModel):
    """Schema request untuk memperbarui domain (partial update).

    Attributes:
        name: Nama domain baru (opsional).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Literasi Informasi Kesehatan",
            }
        }
    )

    name: str | None = Field(default=None, min_length=1, max_length=255)


class DomainResponse(BaseModel):
    """Schema response untuk data domain.

    Attributes:
        id: ID unik domain.
        instrument_id: ID instrumen pemilik domain.
        name: Nama domain.
        created_at: Waktu pembuatan.
        updated_at: Waktu terakhir diperbarui.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                "instrument_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "name": "Literasi Kesehatan",
                "created_at": "2026-05-01T08:00:00",
                "updated_at": "2026-05-01T08:00:00",
            }
        },
    )

    id: str
    instrument_id: str
    name: str
    created_at: datetime
    updated_at: datetime
