"""Schema Pydantic untuk hasil kalkulasi CVI."""

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
