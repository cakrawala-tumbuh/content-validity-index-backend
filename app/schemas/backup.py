"""Schema Pydantic untuk fitur backup dan restore database."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BackupData(BaseModel):
    """Representasi lengkap satu berkas backup database.

    Backup bersifat *logical* (bukan salinan biner file database): seluruh
    baris dari setiap tabel diserialisasi menjadi JSON sehingga portabel
    antar mesin maupun antar engine database.

    Attributes:
        version: Versi format backup, untuk validasi kompatibilitas saat restore.
        created_at: Waktu backup dibuat (UTC).
        tables: Pemetaan nama tabel ke daftar baris; setiap baris berupa dict
            kolom-ke-nilai. Urutan kunci mengikuti dependensi foreign key.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "1.0",
                "created_at": "2026-06-12T08:30:00",
                "tables": {
                    "users": [
                        {
                            "id": "user-1",
                            "email": "admin@example.com",
                            "full_name": "Administrator",
                            "role": "admin",
                            "is_active": True,
                        }
                    ],
                    "instruments": [],
                },
            }
        }
    )

    version: str = Field(description="Versi format backup.")
    created_at: datetime = Field(description="Waktu backup dibuat (UTC).")
    tables: dict[str, list[dict[str, Any]]] = Field(
        description="Pemetaan nama tabel ke daftar baris yang diserialisasi."
    )


class RestoreResponse(BaseModel):
    """Ringkasan hasil operasi restore database.

    Attributes:
        message: Pesan status singkat dalam Bahasa Indonesia.
        tables_restored: Pemetaan nama tabel ke jumlah baris yang dipulihkan.
        total_rows: Total seluruh baris yang dipulihkan dari semua tabel.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Restore database berhasil.",
                "tables_restored": {"users": 3, "instruments": 5, "items": 40},
                "total_rows": 48,
            }
        }
    )

    message: str = Field(description="Pesan status hasil restore.")
    tables_restored: dict[str, int] = Field(description="Jumlah baris yang dipulihkan per tabel.")
    total_rows: int = Field(description="Total baris yang dipulihkan.")
