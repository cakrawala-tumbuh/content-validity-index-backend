"""Integration test untuk pdf_exporter dan endpoint ekspor CVI ke PDF."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_admin
from app.main import app
from app.schemas.cvi import CVIResult, ItemCVIResult
from app.schemas.expert_assignment import AssignmentCreate
from app.schemas.instrument import InstrumentUpdate
from app.schemas.rating import RatingBulkCreate, RatingItem
from app.services.expert_assignment_service import ExpertAssignmentService
from app.services.instrument_service import InstrumentService
from app.services.item_service import ItemService
from app.services.rating_service import RatingService
from app.utils.http_headers import content_disposition_attachment
from app.utils.pdf_exporter import generate_cvi_pdf

from .test_rating_cvi import _setup_instrument_with_items


class TestPdfExporter:
    """Kumpulan test untuk generate_cvi_pdf."""

    def test_generate_pdf_menghasilkan_bytes(self) -> None:
        """generate_cvi_pdf harus menghasilkan bytes PDF yang valid (tidak kosong)."""
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
        pdf_bytes = generate_cvi_pdf(result)
        assert isinstance(pdf_bytes, bytes)
        # magic bytes berkas PDF
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_pdf_instrumen_tanpa_item(self) -> None:
        """generate_cvi_pdf harus tetap berjalan meski tidak ada item."""
        result = CVIResult(
            instrument_id="instr-2",
            instrument_name="Kosong",
            n_experts=0,
            n_items=0,
            items=[],
            s_cvi_ave=0.0,
            s_cvi_ua=0.0,
        )
        pdf_bytes = generate_cvi_pdf(result)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_pdf_content_dengan_karakter_markup(self) -> None:
        """generate_cvi_pdf tidak boleh gagal saat content/domain_id/nama instrumen
        mengandung karakter '&', '<', '>' yang ditafsirkan Paragraph ReportLab
        sebagai mini-markup XML/HTML jika tidak di-escape.
        """
        result = CVIResult(
            instrument_id="instr-3",
            instrument_name="Kepuasan & Kinerja <Tim> A>B",
            n_experts=2,
            n_items=1,
            items=[
                ItemCVIResult(
                    item_id="item-1",
                    sequence_number=1,
                    content="Beban kerja & tekanan waktu (skor < 5 dianggap rendah, > 5 tinggi)",
                    domain_id="Domain A & B",
                    n_experts=2,
                    n_relevant=2,
                    i_cvi=1.0,
                    is_valid=True,
                ),
            ],
            s_cvi_ave=1.0,
            s_cvi_ua=1.0,
        )
        pdf_bytes = generate_cvi_pdf(result)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"


class TestContentDispositionAttachment:
    """Kumpulan test untuk helper content_disposition_attachment."""

    def test_nama_ascii_menghasilkan_filename_biasa(self) -> None:
        """Nama ASCII menghasilkan filename biasa dan aman di-encode Latin-1."""
        value = content_disposition_attachment("CVI_Instrumen.pdf")
        value.encode("latin-1")  # tidak boleh melempar
        assert 'filename="CVI_Instrumen.pdf"' in value

    def test_nama_non_latin1_tetap_aman(self) -> None:
        """Nama dengan em-dash (U+2014) harus tetap menghasilkan header aman Latin-1."""
        value = content_disposition_attachment("CVI_DCS_—_Screening.pdf")
        # WAJIB tidak melempar UnicodeEncodeError (inti bug 500 di produksi).
        value.encode("latin-1")
        # Karakter mentah non-Latin-1 tidak boleh muncul di fallback ASCII.
        assert "—" not in value
        # Nama asli tetap tersedia lewat filename* (RFC 5987, persent-encode UTF-8).
        assert "filename*=UTF-8''" in value
        assert "%E2%80%94" in value  # em-dash ter-encode UTF-8


class TestExportCVIPdfEndpoint:
    """Kumpulan test untuk endpoint GET /instruments/{id}/cvi/export/pdf."""

    async def test_export_pdf_mengembalikan_berkas(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Endpoint harus mengembalikan 200 dengan berkas PDF setelah ada penilaian."""
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "pdf1")

        assign_service = ExpertAssignmentService(db)
        assignment = await assign_service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )

        item_service = ItemService(db)
        items = await item_service.get_by_instrument(instrument_id)

        rating_service = RatingService(db)
        await rating_service.bulk_submit(
            assignment.id,
            expert.id,
            RatingBulkCreate(
                ratings=[RatingItem(item_id=item.id, relevance_score=4) for item in items]
            ),
        )

        app.dependency_overrides[require_admin] = lambda: admin
        try:
            resp = await client.get(f"/api/v1/instruments/{instrument_id}/cvi/export/pdf")
        finally:
            app.dependency_overrides.pop(require_admin, None)

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"
        assert "attachment" in resp.headers["content-disposition"]

    async def test_export_pdf_tanpa_penilaian_raise_400(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Endpoint harus mengembalikan 400 jika instrumen belum ada penilaian."""
        admin, _, instrument_id = await _setup_instrument_with_items(db, "pdf2")

        app.dependency_overrides[require_admin] = lambda: admin
        try:
            resp = await client.get(f"/api/v1/instruments/{instrument_id}/cvi/export/pdf")
        finally:
            app.dependency_overrides.pop(require_admin, None)

        assert resp.status_code == 400

    async def test_export_pdf_instrumen_tidak_ada_raise_404(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Endpoint harus mengembalikan 404 jika instrumen tidak ditemukan."""
        admin, _, _ = await _setup_instrument_with_items(db, "pdf3")

        app.dependency_overrides[require_admin] = lambda: admin
        try:
            resp = await client.get("/api/v1/instruments/nonexistent/cvi/export/pdf")
        finally:
            app.dependency_overrides.pop(require_admin, None)

        assert resp.status_code == 404

    async def test_export_pdf_nama_instrumen_non_latin1(
        self, client: AsyncClient, db: AsyncSession
    ) -> None:
        """Regresi bug produksi: nama instrumen dengan em-dash (U+2014) tidak boleh
        menyebabkan 500 karena header Content-Disposition gagal di-encode Latin-1.
        """
        admin, expert, instrument_id = await _setup_instrument_with_items(db, "pdfemd")

        # Ubah nama instrumen agar mengandung em-dash — persis kasus produksi.
        inst_service = InstrumentService(db)
        await inst_service.update(instrument_id, InstrumentUpdate(name="DCS — Screening"))

        assign_service = ExpertAssignmentService(db)
        assignment = await assign_service.create(
            instrument_id, AssignmentCreate(user_id=expert.id), assigned_by=admin.id
        )
        item_service = ItemService(db)
        items = await item_service.get_by_instrument(instrument_id)
        rating_service = RatingService(db)
        await rating_service.bulk_submit(
            assignment.id,
            expert.id,
            RatingBulkCreate(
                ratings=[RatingItem(item_id=item.id, relevance_score=4) for item in items]
            ),
        )

        app.dependency_overrides[require_admin] = lambda: admin
        try:
            resp = await client.get(f"/api/v1/instruments/{instrument_id}/cvi/export/pdf")
        finally:
            app.dependency_overrides.pop(require_admin, None)

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"
        # Header harus memuat bentuk filename* (RFC 5987) untuk nama non-ASCII.
        assert "filename*=UTF-8''" in resp.headers["content-disposition"]
