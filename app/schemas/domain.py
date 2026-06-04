"""Schema Pydantic untuk entitas Domain."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

HEX_COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"
"""Pola regex untuk validasi warna hex 6 digit (mis. ``#FDE68A``)."""


class DomainCreate(BaseModel):
    """Schema request untuk membuat domain baru dalam sebuah instrumen.

    Attributes:
        name: Nama domain/dimensi.
        construct_definition: Definisi konstruk dari kisi-kisi (kolom D).
        behavioral_indicator_example: Contoh indikator perilaku dari kisi-kisi (kolom E).
        theory_reference: Referensi teori dari kisi-kisi (kolom F).
        background_color: Warna latar dimensi dalam format hex ``#RRGGBB``.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Stability of Change",
                "construct_definition": (
                    "Sejauh mana kebijakan, prosedur, dan praktik kerja tetap stabil "
                    "dari waktu ke waktu."
                ),
                "behavioral_indicator_example": (
                    "Frekuensi perubahan kebijakan; ketersediaan masa transisi."
                ),
                "theory_reference": "Rafferty & Griffin (2006); Judge et al. (1999)",
                "background_color": "#FDE68A",
            }
        }
    )

    name: str = Field(min_length=1, max_length=255)
    construct_definition: str | None = Field(default=None)
    behavioral_indicator_example: str | None = Field(default=None)
    theory_reference: str | None = Field(default=None)
    background_color: str | None = Field(default=None, pattern=HEX_COLOR_PATTERN)


class DomainUpdate(BaseModel):
    """Schema request untuk memperbarui domain (partial update).

    Attributes:
        name: Nama domain baru (opsional).
        construct_definition: Definisi konstruk dari kisi-kisi (kolom D, opsional).
        behavioral_indicator_example: Contoh indikator perilaku dari kisi-kisi (kolom E, opsional).
        theory_reference: Referensi teori dari kisi-kisi (kolom F, opsional).
        background_color: Warna latar dimensi dalam format hex ``#RRGGBB`` (opsional).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Stability of Change",
                "construct_definition": (
                    "Sejauh mana kebijakan, prosedur, dan praktik kerja tetap stabil "
                    "dari waktu ke waktu."
                ),
                "behavioral_indicator_example": (
                    "Frekuensi perubahan kebijakan; ketersediaan masa transisi."
                ),
                "theory_reference": "Rafferty & Griffin (2006); Judge et al. (1999)",
                "background_color": "#FDE68A",
            }
        }
    )

    name: str | None = Field(default=None, min_length=1, max_length=255)
    construct_definition: str | None = Field(default=None)
    behavioral_indicator_example: str | None = Field(default=None)
    theory_reference: str | None = Field(default=None)
    background_color: str | None = Field(default=None, pattern=HEX_COLOR_PATTERN)


class DomainResponse(BaseModel):
    """Schema response untuk data domain.

    Attributes:
        id: ID unik domain.
        instrument_id: ID instrumen pemilik domain.
        name: Nama domain.
        construct_definition: Definisi konstruk dari kisi-kisi (kolom D).
        behavioral_indicator_example: Contoh indikator perilaku dari kisi-kisi (kolom E).
        theory_reference: Referensi teori dari kisi-kisi (kolom F).
        background_color: Warna latar dimensi dalam format hex ``#RRGGBB``.
        created_at: Waktu pembuatan.
        updated_at: Waktu terakhir diperbarui.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                "instrument_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "name": "Stability of Change",
                "construct_definition": (
                    "Sejauh mana kebijakan, prosedur, dan praktik kerja tetap stabil "
                    "dari waktu ke waktu."
                ),
                "behavioral_indicator_example": (
                    "Frekuensi perubahan kebijakan; ketersediaan masa transisi."
                ),
                "theory_reference": "Rafferty & Griffin (2006); Judge et al. (1999)",
                "background_color": "#FDE68A",
                "created_at": "2026-05-01T08:00:00",
                "updated_at": "2026-05-01T08:00:00",
            }
        },
    )

    id: str
    instrument_id: str
    name: str
    construct_definition: str | None
    behavioral_indicator_example: str | None
    theory_reference: str | None
    background_color: str | None
    created_at: datetime
    updated_at: datetime
