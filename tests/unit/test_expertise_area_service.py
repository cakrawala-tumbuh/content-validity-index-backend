"""Unit test untuk ExpertiseAreaService — pengelolaan master bidang keahlian (tanpa DB)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.expertise_area import ExpertiseAreaCreate, ExpertiseAreaUpdate


class TestExpertiseAreaServiceCreate:
    """Kumpulan test untuk method ExpertiseAreaService.create()."""

    @pytest.mark.asyncio
    async def test_create_berhasil(self) -> None:
        """create harus membuat bidang keahlian baru jika nama belum dipakai."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_name.return_value = None
        mock_repo.create.side_effect = lambda area: area

        with patch(
            "app.services.expertise_area_service.ExpertiseAreaRepository",
            return_value=mock_repo,
        ):
            from app.services.expertise_area_service import ExpertiseAreaService

            service = ExpertiseAreaService(mock_db)
            result = await service.create(ExpertiseAreaCreate(name="Statistika"))

        assert result.name == "Statistika"
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_nama_duplikat_raise_409(self) -> None:
        """create harus raise 409 jika nama bidang keahlian sudah ada."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_name.return_value = MagicMock()

        with patch(
            "app.services.expertise_area_service.ExpertiseAreaRepository",
            return_value=mock_repo,
        ):
            from app.services.expertise_area_service import ExpertiseAreaService

            service = ExpertiseAreaService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.create(ExpertiseAreaCreate(name="Statistika"))

        assert exc_info.value.status_code == 409
        mock_repo.create.assert_not_called()


class TestExpertiseAreaServiceGetById:
    """Kumpulan test untuk method ExpertiseAreaService.get_by_id()."""

    @pytest.mark.asyncio
    async def test_get_by_id_tidak_ditemukan_raise_404(self) -> None:
        """get_by_id harus raise 404 jika bidang keahlian tidak ada."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch(
            "app.services.expertise_area_service.ExpertiseAreaRepository",
            return_value=mock_repo,
        ):
            from app.services.expertise_area_service import ExpertiseAreaService

            service = ExpertiseAreaService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.get_by_id("nonexistent")

        assert exc_info.value.status_code == 404


class TestExpertiseAreaServiceUpdate:
    """Kumpulan test untuk method ExpertiseAreaService.update()."""

    @pytest.mark.asyncio
    async def test_update_nama_dan_deskripsi(self) -> None:
        """update harus mengubah nama dan deskripsi bidang keahlian."""
        mock_db = AsyncMock()
        mock_area = MagicMock()
        mock_area.id = "area-1"
        mock_area.name = "Lama"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_area
        mock_repo.get_by_name.return_value = None
        mock_repo.update.return_value = mock_area

        with patch(
            "app.services.expertise_area_service.ExpertiseAreaRepository",
            return_value=mock_repo,
        ):
            from app.services.expertise_area_service import ExpertiseAreaService

            service = ExpertiseAreaService(mock_db)
            await service.update(
                "area-1", ExpertiseAreaUpdate(name="Baru", description="Deskripsi")
            )

        assert mock_area.name == "Baru"
        assert mock_area.description == "Deskripsi"
        mock_repo.update.assert_called_once_with(mock_area)

    @pytest.mark.asyncio
    async def test_update_nama_duplikat_raise_409(self) -> None:
        """update harus raise 409 jika nama baru sudah dipakai bidang keahlian lain."""
        mock_db = AsyncMock()
        mock_area = MagicMock()
        mock_area.id = "area-1"
        mock_area.name = "Lama"

        other = MagicMock()
        other.id = "area-2"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_area
        mock_repo.get_by_name.return_value = other

        with patch(
            "app.services.expertise_area_service.ExpertiseAreaRepository",
            return_value=mock_repo,
        ):
            from app.services.expertise_area_service import ExpertiseAreaService

            service = ExpertiseAreaService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.update("area-1", ExpertiseAreaUpdate(name="Baru"))

        assert exc_info.value.status_code == 409
        mock_repo.update.assert_not_called()


class TestExpertiseAreaServiceDelete:
    """Kumpulan test untuk method ExpertiseAreaService.delete()."""

    @pytest.mark.asyncio
    async def test_delete_berhasil(self) -> None:
        """delete harus menghapus bidang keahlian yang ditemukan."""
        mock_db = AsyncMock()
        mock_area = MagicMock()

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_area

        with patch(
            "app.services.expertise_area_service.ExpertiseAreaRepository",
            return_value=mock_repo,
        ):
            from app.services.expertise_area_service import ExpertiseAreaService

            service = ExpertiseAreaService(mock_db)
            await service.delete("area-1")

        mock_repo.delete.assert_called_once_with(mock_area)

    @pytest.mark.asyncio
    async def test_delete_tidak_ditemukan_raise_404(self) -> None:
        """delete harus raise 404 jika bidang keahlian tidak ada."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch(
            "app.services.expertise_area_service.ExpertiseAreaRepository",
            return_value=mock_repo,
        ):
            from app.services.expertise_area_service import ExpertiseAreaService

            service = ExpertiseAreaService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.delete("nonexistent")

        assert exc_info.value.status_code == 404
