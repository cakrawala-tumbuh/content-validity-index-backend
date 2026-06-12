"""Unit test untuk helper serialisasi BackupService (tanpa DB)."""

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, MetaData, String, Table

from app.services.backup_service import (
    BACKUP_VERSION,
    _deserialize_row,
    _serialize_row,
)


def _sample_table() -> Table:
    """Membuat tabel contoh dengan kolom string, datetime, dan date.

    Returns:
        Definisi Table SQLAlchemy untuk pengujian serialisasi.
    """
    metadata = MetaData()
    return Table(
        "sample",
        metadata,
        Column("id", String),
        Column("created_at", DateTime),
        Column("effective_date", Date),
    )


class TestSerializeRow:
    """Kumpulan test untuk _serialize_row."""

    def test_datetime_dikonversi_ke_iso(self) -> None:
        """Kolom DateTime harus diserialisasi ke string ISO 8601."""
        table = _sample_table()
        dt = datetime(2026, 1, 2, 3, 4, 5)
        row = _serialize_row(
            table, {"id": "a", "created_at": dt, "effective_date": date(2026, 1, 2)}
        )
        assert row["id"] == "a"
        assert row["created_at"] == dt.isoformat()
        assert row["effective_date"] == "2026-01-02"

    def test_nilai_none_dibiarkan(self) -> None:
        """Nilai None pada kolom tanggal harus tetap None."""
        table = _sample_table()
        row = _serialize_row(table, {"id": "a", "created_at": None, "effective_date": None})
        assert row["created_at"] is None
        assert row["effective_date"] is None


class TestDeserializeRow:
    """Kumpulan test untuk _deserialize_row."""

    def test_iso_dikonversi_ke_datetime(self) -> None:
        """String ISO 8601 harus dikembalikan menjadi datetime/date."""
        table = _sample_table()
        dt = datetime(2026, 1, 2, 3, 4, 5)
        row = _deserialize_row(
            table,
            {"id": "a", "created_at": dt.isoformat(), "effective_date": "2026-01-02"},
        )
        assert row["created_at"] == dt
        assert row["effective_date"] == date(2026, 1, 2)

    def test_kolom_tak_dikenal_diabaikan(self) -> None:
        """Kolom yang tidak ada pada tabel harus diabaikan."""
        table = _sample_table()
        row = _deserialize_row(table, {"id": "a", "kolom_asing": 123})
        assert "kolom_asing" not in row
        assert row["id"] == "a"


def test_versi_backup_konstan() -> None:
    """Konstanta versi backup harus bernilai '1.0'."""
    assert BACKUP_VERSION == "1.0"
