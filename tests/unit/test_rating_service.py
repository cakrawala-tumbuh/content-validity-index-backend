"""Unit test untuk RatingService — validasi kepemilikan assignment."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.rating import RatingBulkCreate, RatingItem


class TestRatingServiceValidation:
    """Kumpulan test untuk validasi kepemilikan assignment di RatingService."""

    @pytest.mark.asyncio
    async def test_bulk_submit_assignment_tidak_ditemukan(self) -> None:
        """bulk_submit harus raise 404 jika assignment tidak ditemukan."""
        mock_db = AsyncMock()
        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_id.return_value = None

        with (
            patch(
                "app.services.rating_service.ExpertAssignmentRepository",
                return_value=mock_assignment_repo,
            ),
            patch(
                "app.services.rating_service.RatingRepository",
                return_value=AsyncMock(),
            ),
            patch(
                "app.services.rating_service.ItemRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            data = RatingBulkCreate(ratings=[RatingItem(item_id="item-1", relevance_score=4)])

            with pytest.raises(HTTPException) as exc_info:
                await service.bulk_submit("nonexistent-id", "user-1", data)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_bulk_submit_bukan_expert_yang_ditugaskan(self) -> None:
        """bulk_submit harus raise 403 jika user bukan expert yang di-assign."""
        mock_db = AsyncMock()
        mock_assignment = MagicMock()
        mock_assignment.user_id = "other-user"

        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_id.return_value = mock_assignment

        with (
            patch(
                "app.services.rating_service.ExpertAssignmentRepository",
                return_value=mock_assignment_repo,
            ),
            patch(
                "app.services.rating_service.RatingRepository",
                return_value=AsyncMock(),
            ),
            patch(
                "app.services.rating_service.ItemRepository",
                return_value=AsyncMock(),
            ),
        ):
            from app.services.rating_service import RatingService

            service = RatingService(mock_db)
            data = RatingBulkCreate(ratings=[RatingItem(item_id="item-1", relevance_score=4)])

            with pytest.raises(HTTPException) as exc_info:
                await service.bulk_submit("assignment-1", "user-yang-salah", data)
            assert exc_info.value.status_code == 403
