"""Unit test untuk ExpertAssignmentService — pengelolaan penugasan expert (tanpa DB)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.expert_assignment import AssignmentCreate


class TestExpertAssignmentServiceGetByInstrument:
    """Kumpulan test untuk method ExpertAssignmentService.get_by_instrument()."""

    @pytest.mark.asyncio
    async def test_get_by_instrument_mengembalikan_semua_assignment(self) -> None:
        """get_by_instrument harus mengembalikan semua assignment dalam instrumen."""
        mock_db = AsyncMock()
        mock_assignments = [MagicMock(), MagicMock()]

        mock_repo = AsyncMock()
        mock_repo.get_by_instrument.return_value = mock_assignments

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            result = await service.get_by_instrument("instr-1")

        mock_repo.get_by_instrument.assert_called_once_with("instr-1")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_instrument_tanpa_assignment_mengembalikan_list_kosong(self) -> None:
        """get_by_instrument harus mengembalikan list kosong jika belum ada assignment."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_instrument.return_value = []

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            result = await service.get_by_instrument("instr-kosong")

        assert result == []


class TestExpertAssignmentServiceGetMyAssignments:
    """Kumpulan test untuk method ExpertAssignmentService.get_my_assignments()."""

    @pytest.mark.asyncio
    async def test_get_my_assignments_mengembalikan_assignment_milik_user(self) -> None:
        """get_my_assignments harus mengembalikan assignment milik user yang diberikan."""
        mock_db = AsyncMock()
        mock_assignments = [MagicMock(), MagicMock(), MagicMock()]

        mock_repo = AsyncMock()
        mock_repo.get_by_user.return_value = mock_assignments

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            result = await service.get_my_assignments("expert-1")

        mock_repo.get_by_user.assert_called_once_with("expert-1")
        assert len(result) == 3


class TestExpertAssignmentServiceGetById:
    """Kumpulan test untuk method ExpertAssignmentService.get_by_id()."""

    @pytest.mark.asyncio
    async def test_get_by_id_assignment_ditemukan(self) -> None:
        """get_by_id harus mengembalikan assignment jika ID valid."""
        mock_db = AsyncMock()
        mock_assignment = MagicMock()
        mock_assignment.id = "assign-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            result = await service.get_by_id("assign-1")

        assert result.id == "assign-1"

    @pytest.mark.asyncio
    async def test_get_by_id_tidak_ditemukan_raise_404(self) -> None:
        """get_by_id harus raise HTTPException 404 jika assignment tidak ditemukan."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.get_by_id("nonexistent")

        assert exc_info.value.status_code == 404


class TestExpertAssignmentServiceCreate:
    """Kumpulan test untuk method ExpertAssignmentService.create()."""

    @pytest.mark.asyncio
    async def test_create_berhasil_menugaskan_expert(self) -> None:
        """create harus membuat assignment dan mengembalikannya jika semua valid."""
        mock_db = AsyncMock()
        mock_expert = MagicMock()
        mock_expert.role = "expert"

        mock_assignment = MagicMock()
        mock_assignment.id = "assign-new"
        mock_assignment.instrument_id = "instr-1"
        mock_assignment.user_id = "expert-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_instrument_and_user.return_value = None
        mock_repo.create.return_value = mock_assignment

        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_id.return_value = mock_expert

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=mock_user_repo,
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            data = AssignmentCreate(user_id="expert-1")
            result = await service.create("instr-1", data, assigned_by="admin-1")

        mock_repo.create.assert_called_once()
        assert result.instrument_id == "instr-1"
        assert result.user_id == "expert-1"

    @pytest.mark.asyncio
    async def test_create_user_tidak_ditemukan_raise_404(self) -> None:
        """create harus raise HTTPException 404 jika user tidak ditemukan."""
        mock_db = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_id.return_value = None

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=AsyncMock(),
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=mock_user_repo,
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.create(
                    "instr-1", AssignmentCreate(user_id="nonexistent"), assigned_by="admin-1"
                )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_user_bukan_expert_raise_400(self) -> None:
        """create harus raise HTTPException 400 jika user yang ditugaskan bukan expert."""
        mock_db = AsyncMock()
        mock_admin = MagicMock()
        mock_admin.role = "admin"

        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_id.return_value = mock_admin

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=AsyncMock(),
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=mock_user_repo,
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.create(
                    "instr-1", AssignmentCreate(user_id="admin-2"), assigned_by="admin-1"
                )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_create_expert_sudah_ditugaskan_raise_409(self) -> None:
        """create harus raise HTTPException 409 jika expert sudah ditugaskan ke instrumen."""
        mock_db = AsyncMock()
        mock_expert = MagicMock()
        mock_expert.role = "expert"

        mock_repo = AsyncMock()
        mock_repo.get_by_instrument_and_user.return_value = MagicMock()

        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_id.return_value = mock_expert

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=mock_user_repo,
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.create(
                    "instr-1", AssignmentCreate(user_id="expert-1"), assigned_by="admin-1"
                )

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_create_menyimpan_assignment_id_dengan_benar(self) -> None:
        """create harus meng-generate UUID sebagai ID assignment."""
        import re

        mock_db = AsyncMock()
        mock_expert = MagicMock()
        mock_expert.role = "expert"
        captured: list = []

        async def capture_create(assignment: object) -> object:
            """Menangkap argumen yang diteruskan ke repo.create."""
            captured.append(assignment)
            return assignment

        mock_repo = AsyncMock()
        mock_repo.get_by_instrument_and_user.return_value = None
        mock_repo.create.side_effect = capture_create

        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_id.return_value = mock_expert

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=mock_user_repo,
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            await service.create(
                "instr-1", AssignmentCreate(user_id="expert-1"), assigned_by="admin-1"
            )

        uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
        assert len(captured) == 1
        assert uuid_pattern.match(captured[0].id)


class TestExpertAssignmentServiceDelete:
    """Kumpulan test untuk method ExpertAssignmentService.delete()."""

    @pytest.mark.asyncio
    async def test_delete_berhasil_memanggil_repo_delete(self) -> None:
        """delete harus mengambil assignment lalu memanggil repo.delete."""
        mock_db = AsyncMock()
        mock_assignment = MagicMock()
        mock_assignment.id = "assign-1"

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_assignment

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            await service.delete("assign-1")

        mock_repo.delete.assert_called_once_with(mock_assignment)

    @pytest.mark.asyncio
    async def test_delete_tidak_ditemukan_raise_404(self) -> None:
        """delete harus raise HTTPException 404 jika assignment tidak ditemukan."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        with (
            patch(
                "app.services.expert_assignment_service.ExpertAssignmentRepository",
                return_value=mock_repo,
            ),
            patch(
                "app.services.expert_assignment_service.UserRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.expert_assignment_service import ExpertAssignmentService

            service = ExpertAssignmentService(mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await service.delete("nonexistent")

        assert exc_info.value.status_code == 404
