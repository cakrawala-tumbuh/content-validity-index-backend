"""Schema Pydantic untuk entitas Item."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    """Schema request untuk membuat item baru.

    Attributes:
        sequence_number: Nomor urut item dalam instrumen.
        content: Teks/pernyataan dari item.
        dimension_id: ID dimensi yang mengelompokkan item (opsional).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sequence_number": 1,
                "content": "Remaja mampu mengidentifikasi kebutuhan informasi kesehatannya.",
                "dimension_id": "d1e2f3a4-b5c6-7890-abcd-ef1234567890",
            }
        }
    )

    sequence_number: int = Field(ge=1)
    content: str = Field(min_length=1)
    dimension_id: str | None = Field(default=None, max_length=36)


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
                        "dimension_id": "d1e2f3a4-b5c6-7890-abcd-ef1234567890",
                    },
                    {
                        "sequence_number": 2,
                        "content": "Item kedua.",
                        "dimension_id": "d1e2f3a4-b5c6-7890-abcd-ef1234567890",
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
        dimension_id: ID dimensi baru (opsional).
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
    dimension_id: str | None = Field(default=None, max_length=36)


class ItemResponse(BaseModel):
    """Schema response untuk data item.

    Attributes:
        id: ID unik item.
        instrument_id: ID instrumen yang memiliki item ini.
        sequence_number: Nomor urut item.
        content: Teks/pernyataan item.
        dimension_id: ID dimensi item.
        dimension_name: Nama dimensi item (preloaded).
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
                "dimension_id": "d1e2f3a4-b5c6-7890-abcd-ef1234567890",
                "dimension_name": "Literasi Kesehatan",
                "created_at": "2026-04-01T08:00:00",
                "updated_at": "2026-04-01T08:00:00",
            }
        },
    )

    id: str
    instrument_id: str
    sequence_number: int
    content: str
    dimension_id: str | None
    dimension_name: str | None
    created_at: datetime
    updated_at: datetime
