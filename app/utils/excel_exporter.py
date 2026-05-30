"""Utilitas untuk mengekspor hasil kalkulasi CVI ke format Excel."""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.schemas.cvi import CVIResult


def _hex_fill(hex_color: str) -> PatternFill:
    """Membuat PatternFill solid dari kode warna hex.

    Args:
        hex_color: Kode warna hex tanpa '#' (contoh: 'FFD700').

    Returns:
        Instance PatternFill dengan warna solid.
    """
    return PatternFill(start_color=hex_color, end_color=hex_color, fill_type="solid")


def generate_cvi_excel(result: CVIResult, expert_names: dict[str, str] | None = None) -> bytes:
    """Menghasilkan file Excel berisi hasil kalkulasi CVI.

    Struktur output:
        - Baris 1–2 : Judul instrumen dan informasi umum.
        - Baris 3   : Header tabel.
        - Baris 4+  : Data penilaian per item dengan I-CVI di kolom akhir.
        - Baris N-1 : S-CVI/Ave
        - Baris N   : S-CVI/UA

    Args:
        result: Objek CVIResult berisi hasil kalkulasi lengkap.
        expert_names: Pemetaan user_id ke nama expert (opsional, untuk header kolom).

    Returns:
        Bytes konten file Excel (.xlsx).
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Hasil CVI"  # type: ignore[union-attr]

    HEADER_FILL = _hex_fill("4472C4")
    RESULT_FILL = _hex_fill("D9E1F2")
    BOLD_FONT = Font(bold=True)
    WHITE_FONT = Font(bold=True, color="FFFFFF")
    CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # --- Baris 1: Judul ---
    ws.merge_cells("A1:E1")  # type: ignore[union-attr]
    title_cell = ws["A1"]  # type: ignore[index]
    title_cell.value = f"Hasil Content Validity Index — {result.instrument_name}"
    title_cell.font = Font(bold=True, size=14)
    title_cell.alignment = CENTER

    # --- Baris 2: Info umum ---
    ws["A2"] = "Jumlah Expert:"  # type: ignore[index]
    ws["B2"] = result.n_experts  # type: ignore[index]
    ws["C2"] = "Jumlah Item:"  # type: ignore[index]
    ws["D2"] = result.n_items  # type: ignore[index]
    ws["A2"].font = BOLD_FONT  # type: ignore[index]
    ws["C2"].font = BOLD_FONT  # type: ignore[index]

    # --- Baris 3: Header ---
    headers = ["No", "Domain", "Item", "Jml. Relevan", "I-CVI", "Keterangan"]
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col_idx, value=header)
        cell.font = WHITE_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER

    # --- Baris 4+: Data item ---
    for row_idx, item in enumerate(result.items, start=4):
        ws.cell(row=row_idx, column=1, value=item.sequence_number).alignment = CENTER
        ws.cell(row=row_idx, column=2, value=item.domain or "-")
        ws.cell(row=row_idx, column=3, value=item.content)
        ws.cell(row=row_idx, column=4, value=item.n_relevant).alignment = CENTER
        i_cvi_cell = ws.cell(row=row_idx, column=5, value=item.i_cvi)
        i_cvi_cell.number_format = "0.00"
        i_cvi_cell.alignment = CENTER
        status_text = "Valid" if item.is_valid else "Tidak Valid"
        status_cell = ws.cell(row=row_idx, column=6, value=status_text)
        status_cell.alignment = CENTER
        if not item.is_valid:
            status_cell.font = Font(color="FF0000")

    # --- Baris penutup: S-CVI ---
    last_data_row = 3 + len(result.items)
    s_cvi_ave_row = last_data_row + 2
    s_cvi_ua_row = last_data_row + 3

    for row_num, label, value in [
        (s_cvi_ave_row, "S-CVI/Ave (Average Method)", result.s_cvi_ave),
        (s_cvi_ua_row, "S-CVI/UA (Universal Agreement)", result.s_cvi_ua),
    ]:
        label_cell = ws.cell(row=row_num, column=3, value=label)
        label_cell.font = BOLD_FONT
        label_cell.fill = RESULT_FILL
        value_cell = ws.cell(row=row_num, column=5, value=value)
        value_cell.number_format = "0.00"
        value_cell.font = BOLD_FONT
        value_cell.fill = RESULT_FILL
        value_cell.alignment = CENTER

    # --- Lebar kolom ---
    column_widths = [6, 20, 60, 15, 10, 15]
    for col_idx, width in enumerate(column_widths, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width  # type: ignore[union-attr]

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
