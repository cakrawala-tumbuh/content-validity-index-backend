"""Utilitas untuk mengekspor hasil kalkulasi CVI ke format PDF.

Modul ini merender objek CVIResult menjadi dokumen PDF ringkas yang berisi HANYA
hasil CVI (I-CVI per item, S-CVI/Ave, S-CVI/UA) tanpa data mentah penilaian per
expert. Satu berkas PDF dihasilkan untuk satu hasil kalkulasi CVI sebuah instrumen.
"""

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.cvi import CVIResult, ExpertRatingSummary

_STATUS_LABELS: dict[str, str] = {
    "pending": "Belum Mulai",
    "in_progress": "Sedang Berjalan",
    "completed": "Selesai",
}


def _safe_text(text: str) -> str:
    """Meloloskan teks bebas agar aman dirender oleh Paragraph ReportLab.

    Paragraph ReportLab menafsirkan isi teksnya sebagai mini-markup mirip XML/HTML.
    Teks bebas dari pengguna (nama instrumen, konten item, domain) yang mengandung
    '&', '<', atau '>' akan membuat parser markup tersebut gagal dan melempar
    exception saat build PDF. Fungsi ini meng-escape karakter tersebut lebih dulu.

    Args:
        text: Teks mentah yang akan dirender di dalam sebuah Paragraph.

    Returns:
        Teks yang sudah di-escape, aman dipakai sebagai isi Paragraph.
    """
    return escape(text)


def generate_cvi_pdf(result: CVIResult, expert_names: dict[str, str] | None = None) -> bytes:
    """Menghasilkan berkas PDF berisi hasil kalkulasi CVI sebuah instrumen.

    Struktur output:
        - Judul instrumen dan informasi umum (jumlah expert & item).
        - Tabel I-CVI per item (No, Domain, Item, Jml. Relevan, I-CVI, Keterangan).
        - Ringkasan S-CVI/Ave dan S-CVI/UA.

    Args:
        result: Hasil kalkulasi CVI lengkap (I-CVI per item + skor S-CVI).
        expert_names: Pemetaan opsional user_id ke nama expert. Saat ini tidak
            dirender; disediakan untuk paritas signature dengan generate_cvi_excel.

    Returns:
        Isi berkas PDF sebagai bytes, siap dikirim sebagai respons unduhan.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Hasil CVI - {result.instrument_name}",
    )

    styles = getSampleStyleSheet()
    normal = styles["BodyText"]
    cell_style = ParagraphStyle("cvi_cell", parent=normal, fontSize=9, leading=11)
    header_cell = ParagraphStyle(
        "cvi_header_cell",
        parent=cell_style,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )

    elements: list[Flowable] = []
    elements.append(
        Paragraph(
            f"Hasil Content Validity Index — {_safe_text(result.instrument_name)}",
            styles["Title"],
        )
    )
    n_valid = sum(1 for item in result.items if item.is_valid)
    elements.append(Spacer(1, 6))
    elements.append(
        Paragraph(
            f"Jumlah Expert: {result.n_experts} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Jumlah Item: {result.n_items} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Item Valid: {n_valid} dari {result.n_items}",
            normal,
        )
    )
    elements.append(Spacer(1, 12))

    header = [
        Paragraph(text, header_cell)
        for text in ("No", "Domain", "Item", "Jml. Relevan", "I-CVI", "Keterangan")
    ]
    table_data: list[list[Flowable]] = [header]
    for item in result.items:
        table_data.append(
            [
                Paragraph(str(item.sequence_number), cell_style),
                Paragraph(_safe_text(item.domain_name) if item.domain_name else "-", cell_style),
                Paragraph(_safe_text(item.content), cell_style),
                Paragraph(str(item.n_relevant), cell_style),
                Paragraph(f"{item.i_cvi:.2f}", cell_style),
                Paragraph("Valid" if item.is_valid else "Tidak Valid", cell_style),
            ]
        )

    table = Table(
        table_data,
        colWidths=[12 * mm, 28 * mm, 72 * mm, 20 * mm, 16 * mm, 22 * mm],
        repeatRows=1,
    )
    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]
    )
    for row_idx, item in enumerate(result.items, start=1):
        if not item.is_valid:
            table_style.add("TEXTCOLOR", (5, row_idx), (5, row_idx), colors.HexColor("#dc2626"))
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 14))
    elements.append(Paragraph(f"S-CVI/Ave: {result.s_cvi_ave:.4f}", normal))
    elements.append(Paragraph(f"S-CVI/UA: {result.s_cvi_ua:.4f}", normal))

    doc.build(elements)
    return buffer.getvalue()


def generate_expert_rating_pdf(summary: ExpertRatingSummary, instrument_name: str) -> bytes:
    """Menghasilkan berkas PDF berisi penilaian satu expert untuk sebuah instrumen.

    Struktur output:
        - Judul (nama expert + nama instrumen) dan info umum (institusi, status,
          jumlah item yang sudah dinilai).
        - Tabel penilaian per item (No, Domain, Item, Skor, Relevan, Catatan).

    Args:
        summary: Ringkasan penilaian seorang expert (skor + catatan per item).
        instrument_name: Nama instrumen, ditampilkan di judul dan info berkas.

    Returns:
        Isi berkas PDF sebagai bytes, siap dikirim sebagai respons unduhan.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Penilaian Expert - {summary.expert_name} - {instrument_name}",
    )

    styles = getSampleStyleSheet()
    normal = styles["BodyText"]
    cell_style = ParagraphStyle("expert_cell", parent=normal, fontSize=9, leading=11)
    header_cell = ParagraphStyle(
        "expert_header_cell", parent=cell_style, textColor=colors.white, fontName="Helvetica-Bold"
    )

    elements: list[Flowable] = []
    expert_name_text = _safe_text(summary.expert_name)
    instrument_name_text = _safe_text(instrument_name)
    elements.append(
        Paragraph(
            f"Penilaian Expert — {expert_name_text} — {instrument_name_text}",
            styles["Title"],
        )
    )
    n_rated = sum(1 for r in summary.ratings if r.relevance_score is not None)
    institution_text = _safe_text(summary.institution) if summary.institution else "-"
    status_text = _safe_text(_STATUS_LABELS.get(summary.status, summary.status))
    elements.append(Spacer(1, 6))
    elements.append(
        Paragraph(
            f"Institusi: {institution_text} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Status: {status_text} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Dinilai: {n_rated}/{len(summary.ratings)}",
            normal,
        )
    )
    elements.append(Spacer(1, 12))

    header = [
        Paragraph(text, header_cell)
        for text in ("No", "Domain", "Item", "Skor", "Relevan", "Catatan")
    ]
    table_data: list[list[Flowable]] = [header]
    for rating in summary.ratings:
        score_text = (
            str(rating.relevance_score) if rating.relevance_score is not None else "Belum dinilai"
        )
        relevan_text = (
            "Ya" if rating.is_relevant else ("Tidak" if rating.is_relevant is False else "-")
        )
        table_data.append(
            [
                Paragraph(str(rating.sequence_number), cell_style),
                Paragraph(
                    _safe_text(rating.domain_name) if rating.domain_name else "-", cell_style
                ),
                Paragraph(_safe_text(rating.content), cell_style),
                Paragraph(score_text, cell_style),
                Paragraph(relevan_text, cell_style),
                Paragraph(_safe_text(rating.notes) if rating.notes else "-", cell_style),
            ]
        )

    table = Table(
        table_data,
        colWidths=[10 * mm, 24 * mm, 55 * mm, 18 * mm, 18 * mm, 45 * mm],
        repeatRows=1,
    )
    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]
    )
    for row_idx, rating in enumerate(summary.ratings, start=1):
        if rating.is_relevant is False:
            table_style.add("TEXTCOLOR", (4, row_idx), (4, row_idx), colors.HexColor("#dc2626"))
    table.setStyle(table_style)
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()
