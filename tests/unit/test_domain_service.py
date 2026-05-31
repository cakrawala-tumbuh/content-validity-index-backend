"""Unit test untuk DomainService — operasi CRUD domain instrumen (tanpa DB)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.domain import DomainCreate, DomainUpdate


class TestDomainServiceCreate:
    """Kumpulan test untuk method DomainService.create()."""

    @pytest.mark.asyncio
    async def test_create_berhasil_mengembalikan_domain(self) -> None:
        """create harus memanggil repo.create dan mengembalikan domain yang dibuat."""
        mock_db = AsyncMock()
        mock_domain = MagicMock()
        mock_domain.id = "dom-123"
        mock_domain.instrument_id = "instr-abc"
        mock_domain.name = "Kognitif"

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_domain

        with patch(
            "app.services.domain_service.DomainRepository",
            return_value=mock_repo,
        ):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            data = DomainCreate(name="Kognitif")
            result = await service.create("instr-abc", data)

        mock_repo.create.assert_called_once()
        assert result.name == "Kognitif"
        assert result.instrument_id == "instr-abc"

    @pytest.mark.asyncio
    async def test_create_menyimpan_instrument_id_dan_nama_dengan_benar(self) -> None:
        """create harus menyimpan instrument_id dan name yang diteruskan ke model."""
        mock_db = AsyncMock()
        captured: list = []

        async def capture_create(domain: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(domain)
            return domain

        mock_repo = AsyncMock()
        mock_repo.create.side_effect = capture_create

        with patch(
            "app.services.domain_service.DomainRepository",
            return_value=mock_repo,
        ):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            data = DomainCreate(name="Dimensi Afektif")
            await service.create("instr-xyz", data)

        assert len(captured) == 1
        saved = captured[0]
        assert saved.instrument_id == "instr-xyz"
        assert saved.name == "Dimensi Afektif"

    @pytest.mark.asyncio
    async def test_create_menghasilkan_id_unik(self) -> None:
        """create harus meng-generate UUID sebagai id domain."""
        import re

        mock_db = AsyncMock()
        captured: list = []

        async def capture_create(domain: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(domain)
            return domain

        mock_repo = AsyncMock()
        mock_repo.create.side_effect = capture_create

        with patch(
            "app.services.domain_service.DomainRepository",
            return_value=mock_repo,
        ):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            await service.create("instr-1", DomainCreate(name="Dom A"))
            await service.create("instr-1", DomainCreate(name="Dom B"))

        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )
        id_a = captured[0].id
        id_b = captured[1].id
        assert uuid_pattern.match(id_a), f"ID '{id_a}' bukan UUID valid"
        assert uuid_pattern.match(id_b), f"ID '{id_b}' bukan UUID valid"
        assert id_a != id_b


class TestDomainServiceGetById:
    """Kumpulan test untuk method DomainService.get_by_id()."""

    @pytest.mark.asyncio
    async def test_get_by_id_domain_ditemukan(self) -> None:
        """get_by_id harus mengembalikan domain jika ID dan instrument_id cocok."""
        mock_db = AsyncMock()
        mock_domain = MagicMock()
        mock_domain.id = "dom-1"
        mock_domain.instrument_id = "instr-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_domain

        with patch(
            "app.services.domain_service.DomainRepository",
            return_value=mock_repo,
        ):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            result = await service.get_by_id("dom-1", "instr-1")

        assert result.id == "dom-1"

    @pytest.mark.asyncio
    async def test_get_by_id_tidak_ditemukan_raise_404(self) -> None:
        """get_by_id harus raise HTTPException 404 jika domain tidak ada di DB."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch(
            "app.services.domain_service.DomainRepository",
            return_value=mock_repo,
        ):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.get_by_id("nonexistent", "instr-1")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_by_id_instrument_id_tidak_cocok_raise_404(self) -> None:
        """get_by_id harus raise 404 jika domain ditemukan tapi instrument_id berbeda."""
        mock_db = AsyncMock()
        mock_domain = MagicMock()
        mock_domain.id = "dom-1"
        mock_domain.instrument_id = "instr-lain"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_domain

        with patch(
            "app.services.domain_service.DomainRepository",
            return_value=mock_repo,
        ):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.get_by_id("dom-1", "instr-berbeda")

        assert exc_info.value.status_code == 404


class TestDomainServiceGetByInstrument:
    """Kumpulan test untuk method DomainService.get_by_instrument()."""

    @pytest.mark.asyncio
    async def test_get_by_instrument_mengembalikan_semua_domain(self) -> None:
        """get_by_instrument harus mengembalikan semua domain dalam instrumen."""
        mock_db = AsyncMock()
        mock_domains = [MagicMock(), MagicMock(), MagicMock()]

        mock_repo = AsyncMock()
        mock_repo.get_by_instrument.return_value = mock_domains

        with patch(
            "app.services.domain_service.DomainRepository",
            return_value=mock_repo,
        ):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            result = await service.get_by_instrument("instr-1")

        mock_repo.get_by_instrument.assert_called_once_with("instr-1")
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_by_instrument_tanpa_domain_mengembalikan_list_kosong(self) -> None:
        """get_by_instrument harus mengembalikan list kosong jika tidak ada domain."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_instrument.return_value = []

        with patch(
            "app.services.domain_service.DomainRepository",
            return_value=mock_repo,
        ):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            result = await service.get_by_instrument("instr-kosong")

        assert result == []


class TestDomainServiceUpdate:
    """Kumpulan test untuk method DomainService.update()."""

    @pytest.mark.asyncio
    async def test_update_berhasil_memperbarui_nama(self) -> None:
        """update harus memperbarui nama domain dan memanggil repo.update."""
        mock_db = AsyncMock()
        mock_domain = MagicMock()
        mock_domain.id = "dom-1"
        mock_domain.instrument_id = "instr-1"
        mock_domain.name = "Nama Lama"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_domain
        mock_repo.update.return_value = mock_domain

        with patch("app.services.domain_service.DomainRepository", return_value=mock_repo):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            data = DomainUpdate(name="Nama Baru")
            result = await service.update("dom-1", "instr-1", data)

        assert mock_domain.name == "Nama Baru"
        mock_repo.update.assert_called_once_with(mock_domain)
        assert result is mock_domain

    @pytest.mark.asyncio
    async def test_update_tidak_ditemukan_raise_404(self) -> None:
        """update harus raise HTTPException 404 jika domain tidak ditemukan."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch("app.services.domain_service.DomainRepository", return_value=mock_repo):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.update("nonexistent", "instr-1", DomainUpdate(name="Baru"))

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_name_none_tidak_mengubah_nama(self) -> None:
        """update tidak boleh mengubah nama jika data.name = None."""
        mock_db = AsyncMock()
        mock_domain = MagicMock()
        mock_domain.id = "dom-1"
        mock_domain.instrument_id = "instr-1"
        mock_domain.name = "Nama Tetap"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_domain
        mock_repo.update.return_value = mock_domain

        with patch("app.services.domain_service.DomainRepository", return_value=mock_repo):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            await service.update("dom-1", "instr-1", DomainUpdate(name=None))

        assert mock_domain.name == "Nama Tetap"


class TestDomainServiceDelete:
    """Kumpulan test untuk method DomainService.delete()."""

    @pytest.mark.asyncio
    async def test_delete_berhasil_memanggil_repo_delete(self) -> None:
        """delete harus mengambil domain lalu memanggil repo.delete."""
        mock_db = AsyncMock()
        mock_domain = MagicMock()
        mock_domain.id = "dom-1"
        mock_domain.instrument_id = "instr-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_domain

        with patch("app.services.domain_service.DomainRepository", return_value=mock_repo):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            await service.delete("dom-1", "instr-1")

        mock_repo.delete.assert_called_once_with(mock_domain)

    @pytest.mark.asyncio
    async def test_delete_tidak_ditemukan_raise_404(self) -> None:
        """delete harus raise HTTPException 404 jika domain tidak ditemukan."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch("app.services.domain_service.DomainRepository", return_value=mock_repo):
            from app.services.domain_service import DomainService

            service = DomainService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.delete("nonexistent", "instr-1")

        assert exc_info.value.status_code == 404
