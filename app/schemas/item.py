"""Schema Pydantic untuk entitas Item."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    """Schema request untuk membuat item baru.

    Attributes:
        sequence_number: Nomor urut item dalam instrumen.
        content: Teks/pernyataan dari item.
        domain_id: ID domain/dimensi pengelompokan item (opsional).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sequence_number": 1,
                "content": "Remaja mampu mengidentifikasi kebutuhan informasi kesehatannya.",
                "domain_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
            }
        }
    )

    sequence_number: int = Field(ge=1)
    content: str = Field(min_length=1)
    domain_id: str | None = Field(default=None, max_length=36)


class ItemBulkCreate(BaseModel):
    """Schema request untuk membuat banyak item sekaligus.

    Attributes:
        items: Daftar item yang akan dibuat.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "sequence_number": 1,
                        "content": "Item pertama.",
                        "domain_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                    },
                    {
                        "sequence_number": 2,
                        "content": "Item kedua.",
                        "domain_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                    },
                ]
            }
        }
    )

    items: list[ItemCreate] = Field(min_length=1)


class ItemUpdate(BaseModel):
    """Schema request untuk memperbarui item (partial update).

    Attributes:
        sequence_number: Nomor urut baru (opsional).
        content: Teks baru (opsional).
        domain_id: ID domain baru (opsional, None untuk menghapus).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Remaja mampu mengakses sumber informasi kesehatan yang terpercaya.",
            }
        }
    )

    sequence_number: int | None = Field(default=None, ge=1)
    content: str | None = Field(default=None, min_length=1)
    domain_id: str | None = Field(default=None, max_length=36)


class ItemResponse(BaseModel):
    """Schema response untuk data item.

    Attributes:
        id: ID unik item.
        instrument_id: ID instrumen yang memiliki item ini.
        sequence_number: Nomor urut item.
        content: Teks/pernyataan item.
        domain_id: ID domain/dimensi item.
        created_at: Waktu pembuatan.
        updated_at: Waktu terakhir diperbarui.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "instrument_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "sequence_number": 1,
                "content": "Remaja mampu mengidentifikasi kebutuhan informasi kesehatannya.",
                "domain_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                "created_at": "2026-05-01T08:00:00",
                "updated_at": "2026-05-01T08:00:00",
            }
        },
    )

    id: str
    instrument_id: str
    sequence_number: int
    content: str
    domain_id: str | None
    created_at: datetime
    updated_at: datetime
