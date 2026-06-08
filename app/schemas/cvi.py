"""Schema Pydantic untuk hasil kalkulasi CVI."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemCVIResult(BaseModel):
    """Hasil kalkulasi I-CVI untuk satu item.

    Attributes:
        item_id: ID item.
        sequence_number: Nomor urut item.
        content: Teks item.
        domain_id: ID domain item.
        n_experts: Jumlah expert yang menilai item ini.
        n_relevant: Jumlah expert yang memberi skor 3 atau 4.
        i_cvi: Nilai I-CVI (0.0 – 1.0).
        is_valid: True jika I-CVI memenuhi threshold (≥0.78 untuk ≥8 expert, 1.0 untuk <8).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
                "sequence_number": 1,
                "content": "Remaja mampu mengidentifikasi kebutuhan informasi.",
                "domain_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                "n_experts": 5,
                "n_relevant": 4,
                "i_cvi": 0.8,
                "is_valid": True,
            }
        }
    )

    item_id: str
    sequence_number: int
    content: str
    domain_id: str | None
    n_experts: int
    n_relevant: int
    i_cvi: float = Field(ge=0.0, le=1.0)
    is_valid: bool


class CVIResult(BaseModel):
    """Hasil kalkulasi CVI lengkap untuk sebuah instrumen.

    Attributes:
        instrument_id: ID instrumen.
        instrument_name: Nama instrumen.
        n_experts: Total jumlah expert yang melakukan penilaian.
        n_items: Total jumlah item dalam instrumen.
        items: Hasil I-CVI per item.
        s_cvi_ave: S-CVI metode Average (rata-rata semua I-CVI).
        s_cvi_ua: S-CVI metode Universal Agreement
                  (proporsi item dengan I-CVI = 1.0).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "instrument_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "instrument_name": "YPII v3",
                "n_experts": 5,
                "n_items": 3,
                "items": [],
                "s_cvi_ave": 0.87,
                "s_cvi_ua": 0.67,
            }
        }
    )

    instrument_id: str
    instrument_name: str
    n_experts: int
    n_items: int
    items: list[ItemCVIResult]
    s_cvi_ave: float = Field(ge=0.0, le=1.0)
    s_cvi_ua: float = Field(ge=0.0, le=1.0)


class ItemRatingByExpert(BaseModel):
    """Penilaian seorang expert untuk satu item.

    Attributes:
        item_id: ID item.
        sequence_number: Nomor urut item dalam instrumen.
        content: Teks konten item.
        domain_id: ID domain/dimensi item, atau None jika tanpa domain.
        relevance_score: Skor relevansi 1–4, atau None jika belum dinilai.
        notes: Catatan expert, atau None.
        is_relevant: True jika skor ≥ 3 (relevan), None jika belum dinilai.
    """

    item_id: str
    sequence_number: int
    content: str
    domain_id: str | None
    relevance_score: int | None
    notes: str | None
    is_relevant: bool | None


class ExpertRatingSummary(BaseModel):
    """Ringkasan penilaian seorang expert untuk sebuah instrumen.

    Attributes:
        assignment_id: ID assignment expert.
        user_id: ID user expert.
        expert_name: Nama lengkap expert.
        institution: Institusi expert, atau None.
        status: Status assignment (pending/in_progress/completed).
        deadline: Batas waktu penilaian, atau None.
        ratings: Daftar penilaian per item, terurut berdasarkan sequence_number.
    """

    assignment_id: str
    user_id: str
    expert_name: str
    institution: str | None
    status: str
    deadline: datetime | None
    ratings: list[ItemRatingByExpert]


class InstrumentExpertRatingsResponse(BaseModel):
    """Tampilan penilaian per expert untuk sebuah instrumen.

    Attributes:
        instrument_id: ID instrumen.
        instrument_name: Nama instrumen.
        n_items: Jumlah item dalam instrumen.
        n_experts: Jumlah expert yang di-assign.
        experts: Daftar penilaian per expert, terurut berdasarkan nama.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "instrument_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "instrument_name": "YPII v3",
                "n_items": 3,
                "n_experts": 2,
                "experts": [],
            }
        }
    )

    instrument_id: str
    instrument_name: str
    n_items: int
    n_experts: int
    experts: list[ExpertRatingSummary]
