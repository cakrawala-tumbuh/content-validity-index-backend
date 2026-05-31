"""Unit test untuk ItemService — operasi CRUD item instrumen (tanpa DB)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.item import ItemBulkCreate, ItemCreate, ItemUpdate


class TestItemServiceGetByInstrument:
    """Kumpulan test untuk method ItemService.get_by_instrument()."""

    @pytest.mark.asyncio
    async def test_get_by_instrument_mengembalikan_semua_item(self) -> None:
        """get_by_instrument harus mengembalikan semua item dalam instrumen."""
        mock_db = AsyncMock()
        mock_items = [MagicMock(), MagicMock(), MagicMock()]

        mock_repo = AsyncMock()
        mock_repo.get_by_instrument.return_value = mock_items

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            result = await service.get_by_instrument("instr-1")

        mock_repo.get_by_instrument.assert_called_once_with("instr-1")
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_by_instrument_tanpa_item_mengembalikan_list_kosong(self) -> None:
        """get_by_instrument harus mengembalikan list kosong jika tidak ada item."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_instrument.return_value = []

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            result = await service.get_by_instrument("instr-kosong")

        assert result == []


class TestItemServiceGetById:
    """Kumpulan test untuk method ItemService.get_by_id()."""

    @pytest.mark.asyncio
    async def test_get_by_id_item_ditemukan(self) -> None:
        """get_by_id harus mengembalikan item jika ID dan instrument_id cocok."""
        mock_db = AsyncMock()
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.instrument_id = "instr-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_item

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            result = await service.get_by_id("item-1", "instr-1")

        assert result.id == "item-1"

    @pytest.mark.asyncio
    async def test_get_by_id_tidak_ditemukan_raise_404(self) -> None:
        """get_by_id harus raise HTTPException 404 jika item tidak ada di DB."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.get_by_id("nonexistent", "instr-1")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_by_id_instrument_id_tidak_cocok_raise_404(self) -> None:
        """get_by_id harus raise 404 jika item ditemukan tapi instrument_id berbeda."""
        mock_db = AsyncMock()
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.instrument_id = "instr-lain"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_item

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.get_by_id("item-1", "instr-berbeda")

        assert exc_info.value.status_code == 404


class TestItemServiceCreate:
    """Kumpulan test untuk method ItemService.create()."""

    @pytest.mark.asyncio
    async def test_create_berhasil_mengembalikan_item(self) -> None:
        """create harus memanggil repo.create dan mengembalikan item yang dibuat."""
        mock_db = AsyncMock()
        mock_item = MagicMock()
        mock_item.instrument_id = "instr-1"
        mock_item.content = "Pernyataan baru"

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_item

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            data = ItemCreate(sequence_number=1, content="Pernyataan baru")
            result = await service.create("instr-1", data)

        mock_repo.create.assert_called_once()
        assert result.instrument_id == "instr-1"
        assert result.content == "Pernyataan baru"

    @pytest.mark.asyncio
    async def test_create_menyimpan_semua_field_dengan_benar(self) -> None:
        """create harus meneruskan semua field ke model Item dengan benar."""
        mock_db = AsyncMock()
        captured: list = []

        async def capture_create(item: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(item)
            return item

        mock_repo = AsyncMock()
        mock_repo.create.side_effect = capture_create

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            data = ItemCreate(
                sequence_number=3,
                content="Remaja dapat mengevaluasi informasi.",
                domain_id="dom-abc",
            )
            await service.create("instr-xyz", data)

        assert len(captured) == 1
        saved = captured[0]
        assert saved.instrument_id == "instr-xyz"
        assert saved.sequence_number == 3
        assert saved.content == "Remaja dapat mengevaluasi informasi."
        assert saved.domain_id == "dom-abc"

    @pytest.mark.asyncio
    async def test_create_menghasilkan_id_unik(self) -> None:
        """create harus meng-generate UUID unik sebagai ID item."""
        import re

        mock_db = AsyncMock()
        captured: list = []

        async def capture_create(item: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(item)
            return item

        mock_repo = AsyncMock()
        mock_repo.create.side_effect = capture_create

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            await service.create("instr-1", ItemCreate(sequence_number=1, content="Item A"))
            await service.create("instr-1", ItemCreate(sequence_number=2, content="Item B"))

        uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
        assert uuid_pattern.match(captured[0].id)
        assert uuid_pattern.match(captured[1].id)
        assert captured[0].id != captured[1].id


class TestItemServiceBulkCreate:
    """Kumpulan test untuk method ItemService.bulk_create()."""

    @pytest.mark.asyncio
    async def test_bulk_create_berhasil_membuat_banyak_item(self) -> None:
        """bulk_create harus memanggil repo.bulk_create dan mengembalikan semua item."""
        mock_db = AsyncMock()
        mock_items = [MagicMock(), MagicMock()]

        mock_repo = AsyncMock()
        mock_repo.bulk_create.return_value = mock_items

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            data = ItemBulkCreate(
                items=[
                    ItemCreate(sequence_number=1, content="Item 1"),
                    ItemCreate(sequence_number=2, content="Item 2"),
                ]
            )
            result = await service.bulk_create("instr-1", data)

        mock_repo.bulk_create.assert_called_once()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_bulk_create_menyimpan_instrument_id_ke_semua_item(self) -> None:
        """bulk_create harus menyimpan instrument_id yang sama ke setiap item."""
        mock_db = AsyncMock()
        captured: list = []

        async def capture_bulk_create(items: list) -> list:
            """Menangkap argumen yang diteruskan ke repo.bulk_create."""
            captured.extend(items)
            return items

        mock_repo = AsyncMock()
        mock_repo.bulk_create.side_effect = capture_bulk_create

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            data = ItemBulkCreate(
                items=[
                    ItemCreate(sequence_number=1, content="Item A"),
                    ItemCreate(sequence_number=2, content="Item B"),
                    ItemCreate(sequence_number=3, content="Item C"),
                ]
            )
            await service.bulk_create("instr-target", data)

        assert len(captured) == 3
        assert all(item.instrument_id == "instr-target" for item in captured)


class TestItemServiceUpdate:
    """Kumpulan test untuk method ItemService.update()."""

    @pytest.mark.asyncio
    async def test_update_berhasil_memperbarui_item(self) -> None:
        """update harus memperbarui field item dan memanggil repo.update."""
        mock_db = AsyncMock()
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.instrument_id = "instr-1"
        mock_item.content = "Konten Lama"
        mock_item.sequence_number = 1

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_item
        mock_repo.update.return_value = mock_item

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            data = ItemUpdate(content="Konten Baru", sequence_number=5)
            result = await service.update("item-1", "instr-1", data)

        assert mock_item.content == "Konten Baru"
        assert mock_item.sequence_number == 5
        mock_repo.update.assert_called_once_with(mock_item)
        assert result is mock_item

    @pytest.mark.asyncio
    async def test_update_tidak_ditemukan_raise_404(self) -> None:
        """update harus raise HTTPException 404 jika item tidak ditemukan."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.update("nonexistent", "instr-1", ItemUpdate(content="Baru"))

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_field_none_tidak_mengubah_nilai(self) -> None:
        """update tidak boleh mengubah field yang bernilai None."""
        mock_db = AsyncMock()
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.instrument_id = "instr-1"
        mock_item.content = "Konten Tetap"
        mock_item.sequence_number = 2
        mock_item.domain_id = "dom-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_item
        mock_repo.update.return_value = mock_item

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            await service.update("item-1", "instr-1", ItemUpdate())

        assert mock_item.content == "Konten Tetap"
        assert mock_item.sequence_number == 2
        assert mock_item.domain_id == "dom-1"


class TestItemServiceDelete:
    """Kumpulan test untuk method ItemService.delete()."""

    @pytest.mark.asyncio
    async def test_delete_berhasil_memanggil_repo_delete(self) -> None:
        """delete harus mengambil item lalu memanggil repo.delete."""
        mock_db = AsyncMock()
        mock_item = MagicMock()
        mock_item.id = "item-1"
        mock_item.instrument_id = "instr-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_item

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            await service.delete("item-1", "instr-1")

        mock_repo.delete.assert_called_once_with(mock_item)

    @pytest.mark.asyncio
    async def test_delete_tidak_ditemukan_raise_404(self) -> None:
        """delete harus raise HTTPException 404 jika item tidak ditemukan."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch("app.services.item_service.ItemRepository", return_value=mock_repo):
            from app.services.item_service import ItemService

            service = ItemService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.delete("nonexistent", "instr-1")

        assert exc_info.value.status_code == 404
