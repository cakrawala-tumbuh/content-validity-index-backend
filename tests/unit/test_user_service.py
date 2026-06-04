"""Unit test untuk UserService — sinkronisasi dan pengelolaan data user (tanpa DB)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.user import UserSelfUpdate, UserUpdate


class TestUserServiceSyncFromClaims:
    """Kumpulan test untuk method UserService.sync_from_claims()."""

    @pytest.mark.asyncio
    async def test_sync_membuat_user_baru_jika_belum_ada(self) -> None:
        """sync_from_claims harus membuat user baru jika belum ada di database."""
        mock_db = AsyncMock()
        mock_new_user = MagicMock()
        mock_new_user.id = "user-sub-123"
        mock_new_user.email = "budi@test.com"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None
        mock_repo.create.return_value = mock_new_user

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            claims = {
                "sub": "user-sub-123",
                "email": "budi@test.com",
                "name": "Budi Santoso",
                "groups": [],
            }
            result = await service.sync_from_claims(claims, "admin-group", "expert-group")

        mock_repo.create.assert_called_once()
        mock_repo.update.assert_not_called()
        assert result.id == "user-sub-123"

    @pytest.mark.asyncio
    async def test_sync_memperbarui_user_yang_sudah_ada(self) -> None:
        """sync_from_claims harus memperbarui data user jika sudah ada di database."""
        mock_db = AsyncMock()
        mock_existing_user = MagicMock()
        mock_existing_user.id = "user-sub-456"
        mock_existing_user.email = "lama@test.com"
        mock_existing_user.full_name_overridden = False

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_existing_user
        mock_repo.update.return_value = mock_existing_user

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            claims = {
                "sub": "user-sub-456",
                "email": "baru@test.com",
                "name": "Nama Baru",
                "groups": [],
            }
            await service.sync_from_claims(claims, "admin-group", "expert-group")

        mock_repo.update.assert_called_once()
        mock_repo.create.assert_not_called()
        assert mock_existing_user.email == "baru@test.com"
        assert mock_existing_user.full_name == "Nama Baru"

    @pytest.mark.asyncio
    async def test_sync_tidak_menimpa_full_name_yang_sudah_diedit(self) -> None:
        """sync_from_claims tidak boleh menimpa full_name jika sudah diedit manual."""
        mock_db = AsyncMock()
        mock_existing_user = MagicMock()
        mock_existing_user.id = "user-sub-789"
        mock_existing_user.email = "lama@test.com"
        mock_existing_user.full_name = "Nama Pilihan Pengguna"
        mock_existing_user.full_name_overridden = True

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_existing_user
        mock_repo.update.return_value = mock_existing_user

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            claims = {
                "sub": "user-sub-789",
                "email": "baru@test.com",
                "name": "Nama Dari Authentik",
                "groups": [],
            }
            await service.sync_from_claims(claims, "admin-group", "expert-group")

        # Email tetap disinkronkan, tetapi full_name dipertahankan.
        assert mock_existing_user.email == "baru@test.com"
        assert mock_existing_user.full_name == "Nama Pilihan Pengguna"

    @pytest.mark.asyncio
    async def test_sync_menetapkan_role_admin_dari_grup(self) -> None:
        """sync_from_claims harus menetapkan role admin jika user ada di grup admin."""
        mock_db = AsyncMock()
        captured: list = []

        async def capture_create(user: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(user)
            return user

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None
        mock_repo.create.side_effect = capture_create

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            claims = {
                "sub": "admin-sub",
                "email": "admin@test.com",
                "name": "Admin User",
                "groups": ["cvi-admins"],
            }
            await service.sync_from_claims(claims, "cvi-admins", "cvi-experts")

        assert len(captured) == 1
        assert captured[0].role == "admin"

    @pytest.mark.asyncio
    async def test_sync_menetapkan_role_expert_dari_grup(self) -> None:
        """sync_from_claims harus menetapkan role expert jika user ada di grup expert."""
        mock_db = AsyncMock()
        captured: list = []

        async def capture_create(user: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(user)
            return user

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None
        mock_repo.create.side_effect = capture_create

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            claims = {
                "sub": "expert-sub",
                "email": "expert@test.com",
                "name": "Expert User",
                "groups": ["cvi-experts"],
            }
            await service.sync_from_claims(claims, "cvi-admins", "cvi-experts")

        assert len(captured) == 1
        assert captured[0].role == "expert"

    @pytest.mark.asyncio
    async def test_sync_role_default_expert_jika_tidak_ada_grup(self) -> None:
        """sync_from_claims harus menetapkan role expert jika tidak ada grup yang cocok."""
        mock_db = AsyncMock()
        captured: list = []

        async def capture_create(user: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(user)
            return user

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None
        mock_repo.create.side_effect = capture_create

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            claims = {
                "sub": "user-tanpa-grup",
                "email": "user@test.com",
                "name": "Pengguna Biasa",
                "groups": [],
            }
            await service.sync_from_claims(claims, "cvi-admins", "cvi-experts")

        assert len(captured) == 1
        assert captured[0].role == "expert"


class TestUserServiceGetAll:
    """Kumpulan test untuk method UserService.get_all()."""

    @pytest.mark.asyncio
    async def test_get_all_mengembalikan_semua_user(self) -> None:
        """get_all harus mengembalikan semua user dengan parameter skip dan limit."""
        mock_db = AsyncMock()
        mock_users = [MagicMock(), MagicMock(), MagicMock()]

        mock_repo = AsyncMock()
        mock_repo.get_all.return_value = mock_users

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            result = await service.get_all(skip=0, limit=100)

        mock_repo.get_all.assert_called_once_with(skip=0, limit=100)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_all_mengembalikan_list_kosong(self) -> None:
        """get_all harus mengembalikan list kosong jika tidak ada user."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_all.return_value = []

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            result = await service.get_all()

        assert result == []


class TestUserServiceGetById:
    """Kumpulan test untuk method UserService.get_by_id()."""

    @pytest.mark.asyncio
    async def test_get_by_id_user_ditemukan(self) -> None:
        """get_by_id harus mengembalikan user jika ID valid."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user-abc"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            result = await service.get_by_id("user-abc")

        assert result.id == "user-abc"

    @pytest.mark.asyncio
    async def test_get_by_id_tidak_ditemukan_raise_404(self) -> None:
        """get_by_id harus raise HTTPException 404 jika user tidak ditemukan."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.get_by_id("nonexistent-user")

        assert exc_info.value.status_code == 404
        assert "nonexistent-user" in exc_info.value.detail


class TestUserServiceUpdate:
    """Kumpulan test untuk method UserService.update()."""

    @pytest.mark.asyncio
    async def test_update_berhasil_memperbarui_profil(self) -> None:
        """update harus memperbarui field user dan memanggil repo.update."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.institution = "UI"
        mock_user.is_active = True

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user
        mock_repo.update.return_value = mock_user

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            data = UserUpdate(institution="UGM")
            result = await service.update("user-1", data)

        assert mock_user.institution == "UGM"
        mock_repo.update.assert_called_once_with(mock_user)
        assert result is mock_user

    @pytest.mark.asyncio
    async def test_update_menetapkan_expertise_areas(self) -> None:
        """update harus menetapkan daftar bidang keahlian dari expertise_area_ids."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user-1"

        area_1 = MagicMock()
        area_1.id = "area-1"
        area_2 = MagicMock()
        area_2.id = "area-2"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user
        mock_repo.update.return_value = mock_user

        mock_expertise_repo = AsyncMock()
        mock_expertise_repo.get_by_ids.return_value = [area_1, area_2]

        with (
            patch("app.services.user_service.UserRepository", return_value=mock_repo),
            patch(
                "app.services.user_service.ExpertiseAreaRepository",
                return_value=mock_expertise_repo,
            ),
        ):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            data = UserUpdate(expertise_area_ids=["area-1", "area-2"])
            await service.update("user-1", data)

        assert mock_user.expertise_areas == [area_1, area_2]
        mock_expertise_repo.get_by_ids.assert_called_once_with(["area-1", "area-2"])

    @pytest.mark.asyncio
    async def test_update_expertise_area_tidak_ditemukan_raise_400(self) -> None:
        """update harus raise 400 jika ada expertise_area_id yang tidak ditemukan."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user-1"

        area_1 = MagicMock()
        area_1.id = "area-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user

        mock_expertise_repo = AsyncMock()
        # Hanya satu dari dua ID yang ditemukan.
        mock_expertise_repo.get_by_ids.return_value = [area_1]

        with (
            patch("app.services.user_service.UserRepository", return_value=mock_repo),
            patch(
                "app.services.user_service.ExpertiseAreaRepository",
                return_value=mock_expertise_repo,
            ),
        ):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.update("user-1", UserUpdate(expertise_area_ids=["area-1", "hilang"]))

        assert exc_info.value.status_code == 400
        assert "hilang" in exc_info.value.detail
        mock_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_tidak_ditemukan_raise_404(self) -> None:
        """update harus raise HTTPException 404 jika user tidak ditemukan."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.update("nonexistent", UserUpdate(institution="Baru"))

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_field_none_tidak_mengubah_nilai(self) -> None:
        """update tidak boleh mengubah field yang bernilai None."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.institution = "Institusi Tetap"
        mock_user.is_active = True

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user
        mock_repo.update.return_value = mock_user

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            await service.update("user-1", UserUpdate())

        assert mock_user.institution == "Institusi Tetap"
        assert mock_user.is_active is True

    @pytest.mark.asyncio
    async def test_update_is_active_dapat_diubah(self) -> None:
        """update harus bisa menonaktifkan user dengan is_active=False."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.is_active = True

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user
        mock_repo.update.return_value = mock_user

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            await service.update("user-1", UserUpdate(is_active=False))

        assert mock_user.is_active is False


class TestUserServiceUpdateSelf:
    """Kumpulan test untuk method UserService.update_self()."""

    @pytest.mark.asyncio
    async def test_update_self_mengubah_nama_dan_menandai_overridden(self) -> None:
        """update_self harus mengubah full_name dan menandai full_name_overridden."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.full_name = "Nama Lama"
        mock_user.full_name_overridden = False

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user
        mock_repo.update.return_value = mock_user

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            data = UserSelfUpdate(full_name="Nama Baru", institution="UGM")
            await service.update_self("user-1", data)

        assert mock_user.full_name == "Nama Baru"
        assert mock_user.full_name_overridden is True
        assert mock_user.institution == "UGM"
        mock_repo.update.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_update_self_nama_kosong_raise_400(self) -> None:
        """update_self harus raise HTTPException 400 jika full_name kosong setelah trim."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.update_self("user-1", UserSelfUpdate(full_name="   "))

        assert exc_info.value.status_code == 400
        mock_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_self_tanpa_full_name_tidak_mengubah_flag(self) -> None:
        """update_self tidak mengubah full_name/flag jika full_name tidak dikirim."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.full_name = "Nama Tetap"
        mock_user.full_name_overridden = False

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user
        mock_repo.update.return_value = mock_user

        with patch("app.services.user_service.UserRepository", return_value=mock_repo):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            await service.update_self("user-1", UserSelfUpdate(institution="ITS"))

        assert mock_user.full_name == "Nama Tetap"
        assert mock_user.full_name_overridden is False
        assert mock_user.institution == "ITS"

    @pytest.mark.asyncio
    async def test_update_self_menetapkan_expertise_areas(self) -> None:
        """update_self harus menetapkan bidang keahlian dari expertise_area_ids."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "user-1"

        area = MagicMock()
        area.id = "area-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user
        mock_repo.update.return_value = mock_user

        mock_expertise_repo = AsyncMock()
        mock_expertise_repo.get_by_ids.return_value = [area]

        with (
            patch("app.services.user_service.UserRepository", return_value=mock_repo),
            patch(
                "app.services.user_service.ExpertiseAreaRepository",
                return_value=mock_expertise_repo,
            ),
        ):
            from app.services.user_service import UserService

            service = UserService(mock_db)
            await service.update_self("user-1", UserSelfUpdate(expertise_area_ids=["area-1"]))

        assert mock_user.expertise_areas == [area]
