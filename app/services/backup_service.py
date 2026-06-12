"""Service untuk membuat backup dan memulihkan (restore) data database.

Backup bersifat *logical*: seluruh baris dari setiap tabel ORM diserialisasi
menjadi struktur JSON-friendly, sehingga hasil backup portabel dan tidak
bergantung pada format file biner SQLite. Restore mengganti seluruh isi tabel
dengan data dari backup di dalam satu transaksi.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Table
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Base

#: Versi format backup. Naikkan bila struktur berkas backup berubah.
BACKUP_VERSION = "1.0"


def _serialize_row(table: Table, mapping: dict[str, Any]) -> dict[str, Any]:
    """Mengubah satu baris hasil query menjadi dict yang JSON-friendly.

    Nilai kolom bertipe tanggal/waktu dikonversi ke string ISO 8601 agar dapat
    diserialisasi ke JSON. Tipe lain (str, int, float, bool, dict JSON, None)
    dibiarkan apa adanya.

    Args:
        table: Definisi tabel SQLAlchemy sumber baris.
        mapping: Pemetaan nama kolom ke nilai untuk satu baris.

    Returns:
        Dict baris yang siap diserialisasi ke JSON.
    """
    row: dict[str, Any] = {}
    for column in table.columns:
        value = mapping[column.name]
        if isinstance(column.type, DateTime | Date) and value is not None:
            row[column.name] = value.isoformat()
        else:
            row[column.name] = value
    return row


def _deserialize_row(table: Table, data: dict[str, Any]) -> dict[str, Any]:
    """Mengubah dict baris dari backup menjadi nilai siap-insert.

    Kebalikan dari :func:`_serialize_row`: string ISO 8601 pada kolom
    tanggal/waktu dikembalikan menjadi objek `datetime`/`date` agar kompatibel
    dengan binding parameter SQLAlchemy. Kolom yang tidak dikenal pada tabel
    diabaikan demi ketahanan terhadap perbedaan skema.

    Args:
        table: Definisi tabel SQLAlchemy tujuan baris.
        data: Dict baris hasil deserialisasi JSON dari backup.

    Returns:
        Dict baris dengan nilai yang siap dipakai pada `table.insert()`.
    """
    row: dict[str, Any] = {}
    for column in table.columns:
        if column.name not in data:
            continue
        value = data[column.name]
        if isinstance(column.type, DateTime) and isinstance(value, str):
            row[column.name] = datetime.fromisoformat(value)
        elif isinstance(column.type, Date) and isinstance(value, str):
            row[column.name] = datetime.fromisoformat(value).date()
        else:
            row[column.name] = value
    return row


class BackupService:
    """Service untuk ekspor (backup) dan impor (restore) seluruh data database.

    Args:
        db: AsyncSession database yang aktif.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Inisialisasi BackupService.

        Args:
            db: AsyncSession database yang aktif.
        """
        self.db = db

    async def export_data(self) -> dict[str, Any]:
        """Mengekspor seluruh isi database menjadi struktur backup.

        Iterasi seluruh tabel yang dikelola ORM (mengikuti urutan dependensi
        foreign key), membaca semua baris, lalu menyerialisasinya menjadi
        struktur JSON-friendly.

        Returns:
            Dict backup berisi `version`, `created_at`, dan `tables`.
        """
        tables: dict[str, list[dict[str, Any]]] = {}
        for table in Base.metadata.sorted_tables:
            result = await self.db.execute(table.select())
            tables[table.name] = [
                _serialize_row(table, dict(mapping)) for mapping in result.mappings().all()
            ]
        return {
            "version": BACKUP_VERSION,
            "created_at": datetime.now(UTC).isoformat(),
            "tables": tables,
        }

    async def import_data(self, tables: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
        """Memulihkan database dari data backup.

        Seluruh baris pada setiap tabel ORM dihapus terlebih dahulu (urutan
        terbalik dependensi foreign key), kemudian baris dari backup disisipkan
        (urutan maju). Operasi berlangsung dalam transaksi sesi pemanggil;
        commit/rollback dilakukan oleh dependency `get_db`.

        Args:
            tables: Pemetaan nama tabel ke daftar baris dari backup.

        Returns:
            Pemetaan nama tabel ke jumlah baris yang berhasil dipulihkan.
        """
        # Hapus seluruh data lama dalam urutan terbalik agar tidak melanggar FK.
        for table in reversed(Base.metadata.sorted_tables):
            await self.db.execute(table.delete())

        restored: dict[str, int] = {}
        for table in Base.metadata.sorted_tables:
            rows = tables.get(table.name)
            if not rows:
                continue
            values = [_deserialize_row(table, row) for row in rows]
            await self.db.execute(table.insert(), values)
            restored[table.name] = len(values)
        return restored
