"""Unit test untuk DimensionService — logika validasi & bisnis."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.dimension import DimensionBulkCreate, DimensionCreate, DimensionUpdate


class TestDimensionService:
    """Kumpulan unit test untuk DimensionService."""

    @pytest.mark.asyncio
    async def test_get_by_instrument(self) -> None:
        """Harus mengembalikan daftar dimensi untuk sebuah instrumen."""
        mock_db = AsyncMock()
        mock_dim = AsyncMock()
        mock_dim.id = "dim-1"
        mock_dim.instrument_id = "inst-1"
        mock_dim.name = "Stability of Change"

        mock_repo = AsyncMock()
        mock_repo.get_by_instrument.return_value = [mock_dim]

        with patch(
            "app.services.dimension_service.DimensionRepository",
            return_value=mock_repo,
        ):
            from app.services.dimension_service import DimensionService

            service = DimensionService(mock_db)
            result = await service.get_by_instrument("inst-1")
            assert len(result) == 1
            assert result[0].name == "Stability of Change"
            mock_repo.get_by_instrument.assert_called_once_with("inst-1")

    @pytest.mark.asyncio
    async def test_get_by_id_dimensi_tidak_ditemukan(self) -> None:
        """Harus raise 404 jika dimensi tidak ditemukan."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch(
            "app.services.dimension_service.DimensionRepository",
            return_value=mock_repo,
        ):
            from app.services.dimension_service import DimensionService

            service = DimensionService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.get_by_id("nonexistent", "inst-1")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_by_id_bukan_milik_instrumen(self) -> None:
        """Harus raise 404 jika dimensi bukan milik instrumen yang dimaksud."""
        mock_db = AsyncMock()
        mock_dim = AsyncMock()
        mock_dim.id = "dim-1"
        mock_dim.instrument_id = "inst-2"  # bukan inst-1

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_dim

        with patch(
            "app.services.dimension_service.DimensionRepository",
            return_value=mock_repo,
        ):
            from app.services.dimension_service import DimensionService

            service = DimensionService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.get_by_id("dim-1", "inst-1")
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_dimensi(self) -> None:
        """Harus membuat dimensi baru dengan sukses."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.create.return_value = AsyncMock()

        with patch(
            "app.services.dimension_service.DimensionRepository",
            return_value=mock_repo,
        ):
            from app.services.dimension_service import DimensionService

            service = DimensionService(mock_db)
            data = DimensionCreate(name="Role Clarity", description="Deskripsi role clarity")
            result = await service.create("inst-1", data)
            assert result is not None
            mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_create_dimensi(self) -> None:
        """Harus membuat banyak dimensi sekaligus."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.bulk_create.return_value = [AsyncMock(), AsyncMock()]

        with patch(
            "app.services.dimension_service.DimensionRepository",
            return_value=mock_repo,
        ):
            from app.services.dimension_service import DimensionService

            service = DimensionService(mock_db)
            data = DimensionBulkCreate(
                dimensions=[
                    DimensionCreate(name="Stability of Change"),
                    DimensionCreate(name="Technology Maturity"),
                ]
            )
            result = await service.bulk_create("inst-1", data)
            assert len(result) == 2
            mock_repo.bulk_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_dimensi(self) -> None:
        """Harus memperbarui dimensi dengan data baru."""
        mock_db = AsyncMock()
        mock_dim = AsyncMock()
        mock_dim.id = "dim-1"
        mock_dim.instrument_id = "inst-1"
        mock_dim.name = "Old Name"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_dim
        mock_repo.update.return_value = mock_dim

        with patch(
            "app.services.dimension_service.DimensionRepository",
            return_value=mock_repo,
        ):
            from app.services.dimension_service import DimensionService

            service = DimensionService(mock_db)
            data = DimensionUpdate(name="New Name")
            result = await service.update("dim-1", "inst-1", data)
            assert result.name == "New Name"

    @pytest.mark.asyncio
    async def test_update_dimensi_tidak_ditemukan(self) -> None:
        """Harus raise 404 saat update dimensi yang tidak ada."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch(
            "app.services.dimension_service.DimensionRepository",
            return_value=mock_repo,
        ):
            from app.services.dimension_service import DimensionService

            service = DimensionService(mock_db)
            data = DimensionUpdate(name="New Name")
            with pytest.raises(HTTPException) as exc_info:
                await service.update("nonexistent", "inst-1", data)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_dimensi(self) -> None:
        """Harus menghapus dimensi dengan sukses."""
        mock_db = AsyncMock()
        mock_dim = AsyncMock()
        mock_dim.id = "dim-1"
        mock_dim.instrument_id = "inst-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_dim
        mock_repo.delete.return_value = None

        with patch(
            "app.services.dimension_service.DimensionRepository",
            return_value=mock_repo,
        ):
            from app.services.dimension_service import DimensionService

            service = DimensionService(mock_db)
            await service.delete("dim-1", "inst-1")
            mock_repo.delete.assert_called_once_with(mock_dim)