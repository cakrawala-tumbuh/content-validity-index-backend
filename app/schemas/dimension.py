"""Schema Pydantic untuk entitas Dimension."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DimensionCreate(BaseModel):
    """Schema request untuk membuat dimensi baru.

    Attributes:
        name: Nama dimensi.
        description: Deskripsi dimensi (opsional).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Stability of Change",
                "description": "Dimensi yang mengukur stabilitas perubahan kebijakan di tempat kerja.",
            }
        }
    )

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)


class DimensionUpdate(BaseModel):
    """Schema request untuk memperbarui dimensi.

    Attributes:
        name: Nama dimensi baru (opsional).
        description: Deskripsi dimensi baru (opsional).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Stability of Change (Updated)",
            }
        }
    )

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=500)


class DimensionBulkCreate(BaseModel):
    """Schema request untuk membuat banyak dimensi sekaligus.

    Attributes:
        dimensions: Daftar dimensi yang akan dibuat.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dimensions": [
                    {"name": "Stability of Change"},
                    {"name": "Technology Maturity"},
                    {"name": "Role Clarity"},
                ]
            }
        }
    )

    dimensions: list[DimensionCreate] = Field(min_length=1)


class DimensionResponse(BaseModel):
    """Schema response untuk data dimensi.

    Attributes:
        id: ID unik dimensi.
        instrument_id: ID instrumen yang memiliki dimensi ini.
        name: Nama dimensi.
        description: Deskripsi dimensi.
        created_at: Waktu pembuatan.
        updated_at: Waktu terakhir diperbarui.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "d1e2f3a4-b5c6-7890-abcd-ef1234567890",
                "instrument_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "name": "Stability of Change",
                "description": "Dimensi yang mengukur stabilitas perubahan kebijakan.",
                "created_at": "2026-04-01T08:00:00",
                "updated_at": "2026-04-01T08:00:00",
            }
        },
    )

    id: str
    instrument_id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime