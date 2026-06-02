"""Schema Pydantic untuk entitas Instrument."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InstrumentCreate(BaseModel):
    """Schema request untuk membuat instrumen baru.

    Attributes:
        name: Nama instrumen.
        description: Deskripsi instrumen (opsional).
        version: Versi instrumen (default: "1.0").
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Young Person Information Instrument (YPII)",
                "description": "Instrumen untuk mengukur informasi terkait remaja.",
                "version": "3.0",
            }
        }
    )

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    version: str = Field(default="1.0", max_length=50)


class InstrumentUpdate(BaseModel):
    """Schema request untuk memperbarui instrumen (partial update).

    Attributes:
        name: Nama baru (opsional).
        description: Deskripsi baru (opsional).
        version: Versi baru (opsional).
        status: Status baru: draft | active | closed (opsional).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "active",
            }
        }
    )

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    version: str | None = Field(default=None, max_length=50)
    status: Literal["draft", "active", "closed"] | None = None


class InstrumentResponse(BaseModel):
    """Schema response untuk data instrumen.

    Attributes:
        id: ID unik instrumen.
        name: Nama instrumen.
        description: Deskripsi instrumen.
        version: Versi instrumen.
        status: Status instrumen (draft/active/closed).
        created_by: ID user yang membuat instrumen.
        created_at: Waktu pembuatan.
        updated_at: Waktu terakhir diperbarui.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "name": "Young Person Information Instrument (YPII)",
                "description": "Instrumen untuk mengukur informasi terkait remaja.",
                "version": "3.0",
                "status": "active",
                "created_by": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "created_at": "2026-04-01T08:00:00",
                "updated_at": "2026-04-03T10:00:00",
            }
        },
    )

    id: str
    name: str
    description: str | None
    version: str
    status: str
    created_by: str | None
    created_at: datetime
    updated_at: datetime
