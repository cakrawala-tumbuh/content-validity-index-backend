"""Integration test untuk ActivityLogRepository dan excel_exporter."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.repositories.activity_log_repository import ActivityLogRepository
from app.schemas.cvi import CVIResult, ItemCVIResult
from app.utils.excel_exporter import generate_cvi_excel


class TestActivityLogRepository:
    """Kumpulan test untuk ActivityLogRepository."""

    async def test_create_dan_get_all(self, db: AsyncSession) -> None:
        """Harus bisa menyimpan dan mengambil log aktivitas."""
        import uuid

        repo = ActivityLogRepository(db)
        log = ActivityLog(
            id=str(uuid.uuid4()),
            user_id=None,
            action="test_action",
            resource_type="instrument",
            resource_id="instr-1",
            ip_address="127.0.0.1",
            user_agent="pytest",
            metadata_={"key": "value"},
        )
        await repo.create(log)
        logs = await repo.get_all()
        assert any(log.action == "test_action" for log in logs)

    async def test_filter_by_action(self, db: AsyncSession) -> None:
        """Harus bisa memfilter log berdasarkan action."""
        import uuid

        repo = ActivityLogRepository(db)
        for action in ["login", "logout", "login"]:
            await repo.create(
                ActivityLog(
                    id=str(uuid.uuid4()),
                    action=action,
                    ip_address="127.0.0.1",
                )
            )
        login_logs = await repo.get_all(action="login")
        assert all(log.action == "login" for log in login_logs)
        assert len(login_logs) >= 2


class TestExcelExporter:
    """Kumpulan test untuk generate_cvi_excel."""

    def test_generate_excel_menghasilkan_bytes(self) -> None:
        """generate_cvi_excel harus menghasilkan bytes yang valid (tidak kosong)."""
        result = CVIResult(
            instrument_id="instr-1",
            instrument_name="Instrumen Test",
            n_experts=3,
            n_items=2,
            items=[
                ItemCVIResult(
                    item_id="item-1",
                    sequence_number=1,
                    content="Pertanyaan pertama",
                    domain_id="dom-1",
                    n_experts=3,
                    n_relevant=3,
                    i_cvi=1.0,
                    is_valid=True,
                ),
                ItemCVIResult(
                    item_id="item-2",
                    sequence_number=2,
                    content="Pertanyaan kedua",
                    domain_id=None,
                    n_experts=3,
                    n_relevant=2,
                    i_cvi=0.6667,
                    is_valid=False,
                ),
            ],
            s_cvi_ave=0.8334,
            s_cvi_ua=0.5,
        )
        excel_bytes = generate_cvi_excel(result)
        assert isinstance(excel_bytes, bytes)
        # xlsx magic bytes: PK\x03\x04
        assert excel_bytes[:4] == b"PK\x03\x04"

    def test_generate_excel_instrumen_tanpa_item(self) -> None:
        """generate_cvi_excel harus tetap berjalan meski tidak ada item."""
        result = CVIResult(
            instrument_id="instr-2",
            instrument_name="Kosong",
            n_experts=0,
            n_items=0,
            items=[],
            s_cvi_ave=0.0,
            s_cvi_ua=0.0,
        )
        excel_bytes = generate_cvi_excel(result)
        assert len(excel_bytes) > 0
