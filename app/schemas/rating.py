"""Schema Pydantic untuk entitas Rating."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

#: Skor relevansi yang mewajibkan expert mengisi catatan/alasan.
SCORES_REQUIRING_NOTES: tuple[int, ...] = (1, 2)

#: Pesan error ketika catatan tidak diisi untuk skor relevansi rendah.
NOTES_REQUIRED_MESSAGE: str = (
    "Catatan wajib diisi untuk skor relevansi 1 (Tidak Relevan) atau 2 (Kurang Relevan)."
)


def is_notes_missing(relevance_score: int, notes: str | None) -> bool:
    """Mengecek apakah catatan wajib namun tidak diisi untuk sebuah skor.

    Args:
        relevance_score: Skor relevansi item (1–4).
        notes: Catatan yang diberikan expert (bisa None).

    Returns:
        True jika skor termasuk yang mewajibkan catatan tetapi catatan kosong.
    """
    if relevance_score not in SCORES_REQUIRING_NOTES:
        return False
    return not (notes and notes.strip())


class RatingItem(BaseModel):
    """Schema untuk satu penilaian item dalam bulk submit.

    Attributes:
        item_id: ID item yang dinilai.
        relevance_score: Skor relevansi 1–4.
        notes: Catatan tambahan. Wajib diisi jika skor 1 atau 2.
    """

    item_id: str
    relevance_score: int = Field(ge=1, le=4, description="Skor relevansi 1–4")
    notes: str | None = None

    @model_validator(mode="after")
    def _validate_notes_required(self) -> "RatingItem":
        """Memvalidasi bahwa catatan diisi ketika skor relevansi 1 atau 2.

        Returns:
            Instance RatingItem yang sudah tervalidasi.

        Raises:
            ValueError: Jika skor 1/2 tetapi catatan kosong.
        """
        if is_notes_missing(self.relevance_score, self.notes):
            raise ValueError(NOTES_REQUIRED_MESSAGE)
        return self


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
