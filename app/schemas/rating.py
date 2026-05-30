"""Schema Pydantic untuk entitas Rating."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RatingItem(BaseModel):
    """Schema untuk satu penilaian item dalam bulk submit.

    Attributes:
        item_id: ID item yang dinilai.
        relevance_score: Skor relevansi 1–4.
        notes: Catatan tambahan (opsional).
    """

    item_id: str
    relevance_score: int = Field(ge=1, le=4, description="Skor relevansi 1–4")
    notes: str | None = None


class RatingBulkCreate(BaseModel):
    """Schema request untuk submit semua rating sekaligus.

    Expert mengirimkan seluruh penilaiannya untuk satu assignment
    dalam satu request.

    Attributes:
        ratings: Daftar penilaian per item.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ratings": [
                    {
                        "item_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                        "relevance_score": 4,
                        "notes": "Sangat relevan dengan tujuan instrumen.",
                    },
                    {
                        "item_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                        "relevance_score": 2,
                        "notes": "Perlu direvisi.",
                    },
                ]
            }
        }
    )

    ratings: list[RatingItem] = Field(min_length=1)


class RatingUpdate(BaseModel):
    """Schema request untuk memperbarui satu rating.

    Attributes:
        relevance_score: Skor relevansi baru (opsional).
        notes: Catatan baru (opsional).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "relevance_score": 3,
                "notes": "Setelah dipertimbangkan, cukup relevan.",
            }
        }
    )

    relevance_score: int | None = Field(default=None, ge=1, le=4)
    notes: str | None = None


class RatingResponse(BaseModel):
    """Schema response untuk data rating.

    Attributes:
        id: ID unik rating.
        assignment_id: ID assignment.
        item_id: ID item yang dinilai.
        user_id: ID expert yang menilai.
        relevance_score: Skor relevansi (1–4).
        notes: Catatan expert.
        created_at: Waktu pembuatan.
        updated_at: Waktu terakhir diperbarui.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "e5f6a7b8-c9d0-1234-efab-345678901234",
                "assignment_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                "item_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "relevance_score": 4,
                "notes": "Sangat relevan.",
                "created_at": "2026-05-10T14:00:00",
                "updated_at": "2026-05-10T14:00:00",
            }
        },
    )

    id: str
    assignment_id: str
    item_id: str
    user_id: str
    relevance_score: int
    notes: str | None
    created_at: datetime
    updated_at: datetime
