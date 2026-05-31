"""Unit test untuk ActivityLogService — pengambilan log aktivitas (tanpa DB)."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest


class TestActivityLogServiceGetAll:
    """Kumpulan test untuk method ActivityLogService.get_all()."""

    @pytest.mark.asyncio
    async def test_get_all_tanpa_filter_mengembalikan_semua_log(self) -> None:
        """get_all harus mengembalikan semua log jika tidak ada filter."""
        mock_db = AsyncMock()
        mock_logs = [AsyncMock(), AsyncMock(), AsyncMock()]

        mock_repo = AsyncMock()
        mock_repo.get_all.return_value = mock_logs

        with patch(
            "app.services.activity_log_service.ActivityLogRepository",
            return_value=mock_repo,
        ):
            from app.services.activity_log_service import ActivityLogService

            service = ActivityLogService(mock_db)
            result = await service.get_all()

        mock_repo.get_all.assert_called_once_with(
            user_id=None,
            action=None,
            start_date=None,
            end_date=None,
            skip=0,
            limit=100,
        )
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_all_meneruskan_semua_filter_ke_repo(self) -> None:
        """get_all harus meneruskan semua parameter filter ke repo.get_all."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_all.return_value = []

        start = datetime(2026, 1, 1)
        end = datetime(2026, 6, 30)

        with patch(
            "app.services.activity_log_service.ActivityLogRepository",
            return_value=mock_repo,
        ):
            from app.services.activity_log_service import ActivityLogService

            service = ActivityLogService(mock_db)
            await service.get_all(
                user_id="user-1",
                action="CREATE",
                start_date=start,
                end_date=end,
                skip=10,
                limit=50,
            )

        mock_repo.get_all.assert_called_once_with(
            user_id="user-1",
            action="CREATE",
            start_date=start,
            end_date=end,
            skip=10,
            limit=50,
        )

    @pytest.mark.asyncio
    async def test_get_all_mengembalikan_list_kosong_jika_tidak_ada_log(self) -> None:
        """get_all harus mengembalikan list kosong jika repo mengembalikan list kosong."""
        mock_db = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_all.return_value = []

        with patch(
            "app.services.activity_log_service.ActivityLogRepository",
            return_value=mock_repo,
        ):
            from app.services.activity_log_service import ActivityLogService

            service = ActivityLogService(mock_db)
            result = await service.get_all(user_id="user-tidak-ada")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_filter_berdasarkan_user_id(self) -> None:
        """get_all dengan user_id harus memfilter log berdasarkan pengguna."""
        mock_db = AsyncMock()
        mock_log = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.get_all.return_value = [mock_log]

        with patch(
            "app.services.activity_log_service.ActivityLogRepository",
            return_value=mock_repo,
        ):
            from app.services.activity_log_service import ActivityLogService

            service = ActivityLogService(mock_db)
            result = await service.get_all(user_id="user-tertentu")

        mock_repo.get_all.assert_called_once_with(
            user_id="user-tertentu",
            action=None,
            start_date=None,
            end_date=None,
            skip=0,
            limit=100,
        )
        assert len(result) == 1
