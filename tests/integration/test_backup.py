"""Integration test untuk BackupService dan router backup/restore."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_admin
from app.main import app
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.instrument import InstrumentCreate
from app.services.backup_service import BackupService
from app.services.instrument_service import InstrumentService


async def _seed(db: AsyncSession) -> User:
    """Membuat satu admin dan satu instrumen sebagai data uji.

    Args:
        db: AsyncSession database.

    Returns:
        User admin yang sudah disimpan.
    """
    repo = UserRepository(db)
    admin = await repo.create(
        User(
            id="admin-bk",
            email="bk@example.com",
            full_name="BK Admin",
            role="admin",
            is_active=True,
        )
    )
    instrument_service = InstrumentService(db)
    await instrument_service.create(InstrumentCreate(name="Instrumen Backup"), created_by=admin.id)
    return admin


class TestBackupService:
    """Kumpulan test untuk BackupService."""

    async def test_export_data_berisi_versi_dan_tabel(self, db: AsyncSession) -> None:
        """export_data harus berisi versi, created_at, dan baris tabel terisi."""
        admin = await _seed(db)
        service = BackupService(db)
        data = await service.export_data()
        assert data["version"] == "1.0"
        assert "created_at" in data
        assert any(row["id"] == admin.id for row in data["tables"]["users"])
        assert len(data["tables"]["instruments"]) == 1

    async def test_round_trip_mempertahankan_data(self, db: AsyncSession) -> None:
        """import_data dari hasil export harus mempertahankan jumlah baris."""
        await _seed(db)
        service = BackupService(db)
        data = await service.export_data()
        restored = await service.import_data(data["tables"])
        assert restored["users"] >= 1
        assert restored["instruments"] == 1
        again = await service.export_data()
        assert len(again["tables"]["instruments"]) == 1

    async def test_import_kosong_menghapus_data_lama(self, db: AsyncSession) -> None:
        """import_data dengan backup kosong harus mengosongkan seluruh tabel."""
        await _seed(db)
        service = BackupService(db)
        restored = await service.import_data({})
        assert restored == {}
        data = await service.export_data()
        assert data["tables"]["instruments"] == []
        assert data["tables"]["users"] == []


class TestBackupRouter:
    """Kumpulan test untuk endpoint backup/restore."""

    async def test_download_backup_mengembalikan_berkas(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """GET /backup harus mengembalikan berkas JSON dengan header unduhan."""
        admin = await _seed(db)
        app.dependency_overrides[require_admin] = lambda: admin
        try:
            resp = await client.get("/api/v1/backup/")
        finally:
            app.dependency_overrides.pop(require_admin, None)

        assert resp.status_code == 200
        assert "attachment" in resp.headers["content-disposition"]
        body = resp.json()
        assert body["version"] == "1.0"
        assert "users" in body["tables"]

    async def test_restore_backup_memulihkan_data(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """POST /backup/restore harus memulihkan data dan mengembalikan ringkasan."""
        admin = await _seed(db)
        service = BackupService(db)
        exported = await service.export_data()

        app.dependency_overrides[require_admin] = lambda: admin
        try:
            resp = await client.post("/api/v1/backup/restore", json=exported)
        finally:
            app.dependency_overrides.pop(require_admin, None)

        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Restore database berhasil."
        assert data["total_rows"] >= 2
        assert data["tables_restored"]["instruments"] == 1
