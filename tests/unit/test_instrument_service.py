"""Unit test untuk InstrumentService — operasi CRUD instrumen (tanpa DB)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.instrument import InstrumentCreate, InstrumentUpdate


class TestInstrumentServiceCreate:
    """Kumpulan test untuk method InstrumentService.create()."""

    @pytest.mark.asyncio
    async def test_create_berhasil_mengembalikan_instrumen(self) -> None:
        """create harus memanggil repo.create dan mengembalikan instrumen yang dibuat."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()
        mock_instrument.id = "instr-123"
        mock_instrument.name = "Instrumen Tes"

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_instrument

        with patch(
            "app.services.instrument_service.InstrumentRepository",
            return_value=mock_repo,
        ):
            from app.services.instrument_service import InstrumentService

            service = InstrumentService(mock_db)
            data = InstrumentCreate(name="Instrumen Tes", version="1.0")
            result = await service.create(data, created_by="admin-1")

        mock_repo.create.assert_called_once()
        assert result.id == "instr-123"
        assert result.name == "Instrumen Tes"

    @pytest.mark.asyncio
    async def test_create_menyimpan_semua_field_dengan_benar(self) -> None:
        """create harus meneruskan name, description, version, dan created_by ke model."""
        mock_db = AsyncMock()
        captured: list = []

        async def capture_create(instrument: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(instrument)
            return instrument

        mock_repo = AsyncMock()
        mock_repo.create.side_effect = capture_create

        with patch(
            "app.services.instrument_service.InstrumentRepository",
            return_value=mock_repo,
        ):
            from app.services.instrument_service import InstrumentService

            service = InstrumentService(mock_db)
            data = InstrumentCreate(name="Tes Nama", description="Deskripsi Tes", version="2.0")
            await service.create(data, created_by="user-abc")

        assert len(captured) == 1
        saved = captured[0]
        assert saved.name == "Tes Nama"
        assert saved.description == "Deskripsi Tes"
        assert saved.version == "2.0"
        assert saved.created_by == "user-abc"

    @pytest.mark.asyncio
    async def test_create_deskripsi_none_diperbolehkan(self) -> None:
        """create harus berhasil ketika description tidak diisi (None)."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()
        mock_instrument.description = None

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_instrument

        with patch(
            "app.services.instrument_service.InstrumentRepository",
            return_value=mock_repo,
        ):
            from app.services.instrument_service import InstrumentService

            service = InstrumentService(mock_db)
            data = InstrumentCreate(name="Instrumen Tanpa Deskripsi")
            result = await service.create(data, created_by="admin-x")

        assert result.description is None


class TestInstrumentServiceGetById:
    """Kumpulan test untuk method InstrumentService.get_by_id()."""

    @pytest.mark.asyncio
    async def test_get_by_id_instrumen_ditemukan(self) -> None:
        """get_by_id harus mengembalikan instrumen jika ID valid."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()
        mock_instrument.id = "instr-abc"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_instrument

        with patch(
            "app.services.instrument_service.InstrumentRepository",
            return_value=mock_repo,
        ):
            from app.services.instrument_service import InstrumentService

            service = InstrumentService(mock_db)
            result = await service.get_by_id("instr-abc")

        assert result.id == "instr-abc"

    @pytest.mark.asyncio
    async def test_get_by_id_tidak_ditemukan_raise_404(self) -> None:
        """get_by_id harus raise HTTPException 404 jika instrumen tidak ada."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch(
            "app.services.instrument_service.InstrumentRepository",
            return_value=mock_repo,
        ):
            from app.services.instrument_service import InstrumentService

            service = InstrumentService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.get_by_id("nonexistent-id")

        assert exc_info.value.status_code == 404
        assert "nonexistent-id" in exc_info.value.detail


class TestInstrumentServiceGetAll:
    """Kumpulan test untuk method InstrumentService.get_all()."""

    @pytest.mark.asyncio
    async def test_get_all_admin_mengambil_semua_instrumen(self) -> None:
        """Admin harus mendapat semua instrumen via repo.get_all."""
        mock_db = AsyncMock()
        mock_instruments = [MagicMock(), MagicMock()]

        mock_repo = AsyncMock()
        mock_repo.get_all.return_value = mock_instruments

        with patch(
            "app.services.instrument_service.InstrumentRepository",
            return_value=mock_repo,
        ):
            from app.services.instrument_service import InstrumentService

            service = InstrumentService(mock_db)
            result = await service.get_all(user_id="admin-1", role="admin")

        mock_repo.get_all.assert_called_once()
        mock_repo.get_by_user_assignments.assert_not_called()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_all_expert_hanya_instrumen_yang_di_assign(self) -> None:
        """Expert hanya mendapat instrumen yang di-assign kepadanya."""
        mock_db = AsyncMock()
        mock_instruments = [MagicMock()]

        mock_repo = AsyncMock()
        mock_repo.get_by_user_assignments.return_value = mock_instruments

        with patch(
            "app.services.instrument_service.InstrumentRepository",
            return_value=mock_repo,
        ):
            from app.services.instrument_service import InstrumentService

            service = InstrumentService(mock_db)
            result = await service.get_all(user_id="expert-1", role="expert")

        mock_repo.get_by_user_assignments.assert_called_once_with(
            user_id="expert-1", skip=0, limit=100
        )
        mock_repo.get_all.assert_not_called()
        assert len(result) == 1


class TestInstrumentServiceUpdate:
    """Kumpulan test untuk method InstrumentService.update()."""

    @pytest.mark.asyncio
    async def test_update_berhasil_memperbarui_instrumen(self) -> None:
        """update harus memperbarui field instrumen dan memanggil repo.update."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()
        mock_instrument.id = "instr-1"
        mock_instrument.name = "Nama Lama"
        mock_instrument.status = "draft"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_instrument
        mock_repo.update.return_value = mock_instrument

        with patch(
            "app.services.instrument_service.InstrumentRepository",
            return_value=mock_repo,
        ):
            from app.services.instrument_service import InstrumentService

            service = InstrumentService(mock_db)
            data = InstrumentUpdate(name="Nama Baru", status="active")
            result = await service.update("instr-1", data)

        assert mock_instrument.name == "Nama Baru"
        assert mock_instrument.status == "active"
        mock_repo.update.assert_called_once_with(mock_instrument)
        assert result is mock_instrument

    @pytest.mark.asyncio
    async def test_update_tidak_ditemukan_raise_404(self) -> None:
        """update harus raise HTTPException 404 jika instrumen tidak ditemukan."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch(
            "app.services.instrument_service.InstrumentRepository",
            return_value=mock_repo,
        ):
            from app.services.instrument_service import InstrumentService

            service = InstrumentService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.update("nonexistent", InstrumentUpdate(name="Baru"))

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_field_none_tidak_mengubah_nilai(self) -> None:
        """update tidak boleh mengubah field yang bernilai None."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()
        mock_instrument.id = "instr-1"
        mock_instrument.name = "Nama Tetap"
        mock_instrument.description = "Deskripsi Tetap"
        mock_instrument.version = "1.0"
        mock_instrument.status = "draft"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_instrument
        mock_repo.update.return_value = mock_instrument

        with patch(
            "app.services.instrument_service.InstrumentRepository",
            return_value=mock_repo,
        ):
            from app.services.instrument_service import InstrumentService

            service = InstrumentService(mock_db)
            await service.update("instr-1", InstrumentUpdate())

        assert mock_instrument.name == "Nama Tetap"
        assert mock_instrument.description == "Deskripsi Tetap"
        assert mock_instrument.version == "1.0"
        assert mock_instrument.status == "draft"


class TestInstrumentServiceDelete:
    """Kumpulan test untuk method InstrumentService.delete()."""

    @pytest.mark.asyncio
    async def test_delete_berhasil_memanggil_repo_delete(self) -> None:
        """delete harus mengambil instrumen lalu memanggil repo.delete."""
        mock_db = AsyncMock()
        mock_instrument = MagicMock()
        mock_instrument.id = "instr-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_instrument

        with patch(
            "app.services.instrument_service.InstrumentRepository",
            return_value=mock_repo,
        ):
            from app.services.instrument_service import InstrumentService

            service = InstrumentService(mock_db)
            await service.delete("instr-1")

        mock_repo.delete.assert_called_once_with(mock_instrument)

    @pytest.mark.asyncio
    async def test_delete_tidak_ditemukan_raise_404(self) -> None:
        """delete harus raise HTTPException 404 jika instrumen tidak ditemukan."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch(
            "app.services.instrument_service.InstrumentRepository",
            return_value=mock_repo,
        ):
            from app.services.instrument_service import InstrumentService

            service = InstrumentService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.delete("nonexistent")

        assert exc_info.value.status_code == 404
