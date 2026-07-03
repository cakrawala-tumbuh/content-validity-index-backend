"""Utilitas untuk membangun nilai header HTTP yang aman di-encode.

Nilai header HTTP wajib dapat di-encode Latin-1 (ISO-8859-1). Nama file unduhan
yang diturunkan dari data pengguna (mis. nama instrumen) dapat mengandung
karakter di luar Latin-1 — contohnya em-dash ``—`` (U+2014) — yang membuat
Starlette/uvicorn melempar ``UnicodeEncodeError`` saat menulis header dan
menghasilkan HTTP 500. Modul ini membangun ``Content-Disposition`` yang aman.
"""

from urllib.parse import quote


def content_disposition_attachment(filename: str) -> str:
    """Membangun nilai header Content-Disposition untuk lampiran unduhan.

    Menghasilkan dua bentuk sekaligus sesuai RFC 6266/5987:
    - ``filename="..."`` berisi fallback ASCII (karakter non-ASCII diganti ``_``),
      agar aman di-encode Latin-1 pada klien lama.
    - ``filename*=UTF-8''...`` berisi nama asli ter-persent-encode UTF-8, yang
      dipakai browser modern untuk menampilkan nama file sebenarnya.

    Args:
        filename: Nama file yang diinginkan (boleh mengandung karakter non-ASCII).

    Returns:
        Nilai header Content-Disposition yang selalu aman di-encode Latin-1.
    """
    ascii_fallback = "".join(
        char if (char.isascii() and char.isprintable() and char != '"') else "_"
        for char in filename
    )
    quoted_utf8 = quote(filename, safe="")
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quoted_utf8}"
