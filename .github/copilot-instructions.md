# Content Validity Index Backend — Copilot Instructions

> **PERHATIAN UNTUK AI:** Instruksi ini bersifat **WAJIB** dan **MENGIKAT**.
> Sebelum mengerjakan tugas apa pun, baca seluruh instruksi ini.
> Sebelum menyelesaikan tugas apa pun, verifikasi setiap item pada **Checklist Kepatuhan** di bawah.
> Melanggar instruksi ini adalah **kesalahan serius** — perbaiki segera sebelum melanjutkan.

---

## Checklist Kepatuhan — WAJIB Diverifikasi Setiap Selesai Mengerjakan Tugas

AI **HARUS** memverifikasi setiap poin berikut sebelum menyatakan suatu pekerjaan selesai.
Tandai setiap poin secara mental. Jika ada yang belum terpenuhi, **selesaikan dulu** sebelum lanjut.

### ✅ Checklist Kode

- [ ] Semua fungsi, method, class, dan modul baru/diubah sudah memiliki **docstring Google Style**.
- [ ] Semua parameter fungsi dan return value sudah menggunakan **type hints**.
- [ ] Tidak ada string SQL yang diinterpolasi secara manual — semua query melalui **SQLAlchemy ORM**.
- [ ] Tidak ada secret/credential yang di-hardcode di dalam kode — semua dari **environment variable**.
- [ ] Panjang baris tidak melebihi **100 karakter**.
- [ ] Semua operasi I/O (DB, HTTP) menggunakan **`async/await`**.
- [ ] Semua input dari request divalidasi melalui **Pydantic schema**.
- [ ] Tidak ada detail stack trace yang terekspos pada response error di production.

### ✅ Checklist Testing

- [ ] Sudah ada unit test untuk setiap kode baru/diubah di `tests/unit/`.
- [ ] Docker image sudah di-build ulang: `docker build -t cvi-backend:test .`
- [ ] Test sudah dijalankan di dalam Docker dan **semua test lolos**:
  `docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test`
- [ ] Coverage kode di `app/` tidak turun di bawah **80%**.

### ✅ Checklist Dokumentasi API

- [ ] Setiap endpoint baru/diubah memiliki `summary`, `description`, `response_model`, dan `responses`.
- [ ] Setiap Pydantic schema baru/diubah memiliki `model_config` dengan `json_schema_extra` berisi contoh data.

### ✅ Checklist Git

- [ ] Commit message ditulis dalam **Bahasa Indonesia**.
- [ ] Format commit mengikuti: `<tipe>(<scope>): <deskripsi singkat>`.
- [ ] Tipe commit sesuai dengan perubahan yang dilakukan (feat/fix/docs/test/refactor/chore/style/perf).
- [ ] Semua commit di lokal **WAJIB** dilakukan di branch `master`.
- [ ] Push menyesuaikan instruksi:
      - Jika diminta push ke master: `git push origin master`.
      - Jika diminta buat PR: push master lokal ke branch baru di GitHub lalu `gh pr create`.

### ✅ Checklist Docker & Keamanan

- [ ] Dockerfile menggunakan **multi-stage build** (stage `builder` + stage `runtime`).
- [ ] Image final tidak menyertakan file test, `.env`, atau credential.
- [ ] File `.env` tidak pernah di-commit ke repository.

---

## Ringkasan Proyek

Backend REST API berbasis **FastAPI** untuk pengelolaan **Content Validity Index (CVI)**.
CVI adalah metode statistik yang digunakan untuk mengukur validitas isi suatu instrumen penelitian,
dengan menghitung rasio persetujuan antar-penilai (expert) terhadap item-item dalam instrumen.

## Tech Stack

| Komponen | Teknologi |
|---|---|
| Framework | FastAPI |
| Bahasa | Python 3.11+ |
| Validasi | Pydantic v2 |
| Database | PostgreSQL (via SQLAlchemy + asyncpg) |
| Migrasi DB | Alembic |
| Testing | pytest + pytest-asyncio + httpx |
| Linter/Formatter | Ruff |
| Type Checker | mypy |
| Container | Docker + Docker Compose |
| Dokumentasi API | Swagger UI (bawaan FastAPI) / ReDoc |
| CI/CD | GitHub Actions |
| Container Registry | GitHub Container Registry (GHCR) |
| CLI GitHub | GitHub CLI (`gh`) |

## Struktur Proyek

```
content-validity-index-backend/
├── .github/
│   ├── copilot-instructions.md   # file ini
│   ├── workflows/
│   │   ├── lint.yml              # linter (push/PR ke master)
│   │   ├── test.yml              # unit test (push/PR ke master)
│   │   ├── release.yml           # GitHub Release (tag di master)
│   │   └── docker-publish.yml   # build & push ke GHCR (tag di master)
│   └── instructions/
│       └── *.instructions.md
├── app/
│   ├── __init__.py
│   ├── main.py                  # entrypoint FastAPI
│   ├── config.py                # konfigurasi (Settings via pydantic-settings)
│   ├── database.py              # koneksi async SQLAlchemy
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic schemas (request/response)
│   ├── routers/                 # FastAPI routers (endpoint per domain)
│   ├── services/                # business logic
│   ├── repositories/            # akses data (repository pattern)
│   └── utils/                   # helper / utilitas
├── tests/
│   ├── conftest.py              # fixtures pytest
│   ├── unit/                    # unit test (tanpa DB)
│   └── integration/             # integration test (dengan DB test)
├── alembic/
│   ├── env.py
│   └── versions/
├── .env.example                 # contoh environment variables
├── .ruff.toml                   # konfigurasi Ruff
├── mypy.ini                     # konfigurasi mypy
├── pyproject.toml               # dependensi & konfigurasi build
├── Dockerfile
├── docker-compose.yml           # untuk development lokal
├── docker-compose.test.yml      # untuk menjalankan test di Docker
└── README.md
```

## Standar Kode

> **ATURAN MUTLAK:** AI **DILARANG** menulis atau mengubah kode tanpa terlebih dahulu memastikan
> semua standar di bagian ini terpenuhi. Tidak ada pengecualian.

### Docstring

**Setiap** fungsi, method, class, dan modul **WAJIB** memiliki docstring dalam format Google Style.
Ini berlaku untuk kode baru **maupun kode yang diubah** — tidak ada pengecualian.
AI **DILARANG** melewatkan docstring dengan alasan apapun, termasuk kode yang tampak "sederhana".

```python
def calculate_cvi(ratings: list[int], n_experts: int) -> float:
    """Menghitung Content Validity Index (CVI) dari penilaian para ahli.

    CVI dihitung sebagai jumlah penilaian yang relevan (nilai 3 atau 4)
    dibagi dengan total jumlah penilai.

    Args:
        ratings: Daftar skor penilaian dari setiap ahli (skala 1–4).
        n_experts: Jumlah total ahli penilai.

    Returns:
        Nilai CVI antara 0.0 sampai 1.0.

    Raises:
        ValueError: Jika `n_experts` bernilai nol atau negatif.

    Example:
        >>> calculate_cvi([3, 4, 2, 4], n_experts=4)
        0.75
    """
```

### Gaya Kode

- **WAJIB** gunakan **type hints** di semua parameter fungsi dan return value — kode tanpa type hints **TIDAK BOLEH** di-commit.
- **WAJIB** gunakan **Ruff** sebagai linter dan formatter (menggantikan Black + isort + flake8).
- **WAJIB** jalankan `ruff check . --fix` dan `ruff format .` sebelum setiap commit.
- **WAJIB** pastikan `mypy .` tidak menghasilkan error sebelum commit.
- Panjang baris maksimal: **100 karakter** — **TIDAK BOLEH** dilanggar.
- **WAJIB** gunakan `async/await` untuk semua operasi I/O (DB, HTTP) — kode sinkron untuk I/O **DILARANG**.

### Keamanan (OWASP Top 10)

> **PERINGATAN:** Pelanggaran keamanan adalah kesalahan kritis. AI **HARUS** memprioritaskan
> keamanan di atas segalanya dan **WAJIB** memeriksa setiap poin berikut pada setiap perubahan kode.

- **WAJIB** validasi semua input melalui Pydantic schema — **DILARANG** mempercayai data mentah dari request.
- **WAJIB** gunakan parameterized queries melalui SQLAlchemy ORM — **DILARANG** interpolasi string SQL dalam bentuk apapun.
- **WAJIB** simpan semua secret di environment variable — **DILARANG KERAS** hardcode credential, API key, atau secret di kode.
- **WAJIB** terapkan rate limiting pada endpoint publik.
- **WAJIB** gunakan HTTPS di production (tangani di reverse proxy / load balancer).
- **DILARANG** mengekspos detail stack trace pada response error di production.

## Alur Testing

> **ATURAN MUTLAK:** AI **DILARANG** menyatakan suatu pekerjaan selesai sebelum test lolos
> di lingkungan Docker. Ini berlaku tanpa pengecualian untuk setiap penambahan atau perubahan kode.

### Prinsip

Setiap kali ada **penambahan atau perubahan kode**, AI **WAJIB** menjalankan urutan berikut:

```bash
# 1. WAJIB: Build Docker image lokal
docker build -t cvi-backend:test .

# 2. WAJIB: Jalankan test menggunakan image tersebut
docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test
```

Jika ada test yang gagal, AI **HARUS** memperbaiki kode terlebih dahulu sebelum melanjutkan.
AI **DILARANG** melewati langkah ini dengan alasan apapun.

### Struktur Test

- `tests/unit/` — test tanpa dependensi eksternal (DB, HTTP). **WAJIB** mock semua I/O.
- `tests/integration/` — test dengan database PostgreSQL test (via Docker Compose).
- Coverage minimum: **80%** untuk kode di `app/` — **TIDAK BOLEH** dikurangi.

## Alur Git

> **ATURAN MUTLAK:** AI **WAJIB** mengikuti seluruh konvensi Git di bagian ini.
> Commit message dalam bahasa selain Indonesia dan push ke `master` tanpa izin eksplisit
> adalah **pelanggaran serius** yang harus dihindari.

### Bahasa Commit

Semua commit message **WAJIB** ditulis dalam **Bahasa Indonesia** dengan format:

```
<tipe>(<scope>): <deskripsi singkat>

<penjelasan opsional yang lebih detail, jika perlu>
```

**Tipe commit yang valid:**

| Tipe | Kapan digunakan |
|---|---|
| `feat` | Menambahkan fitur baru |
| `fix` | Memperbaiki bug |
| `docs` | Perubahan dokumentasi saja |
| `test` | Menambah atau mengubah test |
| `refactor` | Refaktor kode tanpa menambah fitur atau memperbaiki bug |
| `chore` | Perubahan tooling, dependensi, konfigurasi CI |
| `style` | Perubahan format/style (tidak mengubah logika) |
| `perf` | Peningkatan performa |

**Contoh:**
```
feat(cvi): tambahkan endpoint kalkulasi CVI per item

Endpoint POST /api/v1/cvi/calculate menerima daftar skor
dari beberapa expert dan mengembalikan nilai CVI per item
beserta interpretasinya.
```

### Strategi Branch

| Branch | Deskripsi |
|---|---|
| `master` | Branch utama, selalu stabil dan siap rilis |

- Semua commit di lokal **WAJIB** dilakukan di branch `master`.
- **DILARANG** menggunakan branch lokal selain `master`.
- Ketika push, ikuti instruksi pengguna:
  - **Jika diminta push ke master**: `git push origin master`.
  - **Jika diminta buat PR**: push dari master lokal ke branch baru di GitHub, lalu `gh pr create`.
- **WAJIB** gunakan `gh pr create` untuk membuat PR — jangan gunakan cara lain.

### Kebijakan Tagging (Semantic Versioning)

Format tag: `vMAJOR.MINOR.PATCH`

| Komponen | Kondisi naik |
|---|---|
| `MAJOR` | Perubahan breaking (API tidak kompatibel ke belakang, migrasi DB destruktif) |
| `MINOR` | Penambahan fitur baru yang backward-compatible (endpoint baru, model baru) |
| `PATCH` | Perbaikan bug, pembaruan dependensi minor, perubahan dokumentasi |

**Cara membuat tag:**
```bash
# Buat tag di master
git tag -a v1.2.0 -m "Rilis v1.2.0: tambahkan fitur kalkulasi S-CVI"
git push origin v1.2.0

# Atau gunakan GitHub CLI
gh release create v1.2.0 --title "v1.2.0" --notes "..."
```

Tag **HARUS** selalu berada di commit di branch `master` — **DILARANG** membuat tag di branch lain.

## GitHub Actions

### Pemicu Workflow

| Workflow | Pemicu |
|---|---|
| `lint.yml` | Push ke `master`, PR ke `master` |
| `test.yml` | Push ke `master`, PR ke `master` |
| `release.yml` | Push tag `v*` di `master` |
| `docker-publish.yml` | Push tag `v*` di `master` |

### Interaksi dengan GitHub

**WAJIB** selalu gunakan **GitHub CLI (`gh`)** untuk semua interaksi dengan GitHub.
**DILARANG** menggunakan cara lain (misalnya git remote langsung untuk operasi yang bisa dilakukan via `gh`).

| Operasi | Perintah yang WAJIB digunakan |
|---|---|
| Membuat PR | `gh pr create` |
| Membuat release | `gh release create` |
| Melihat status CI | `gh run list` / `gh run view` |
| Memeriksa PR | `gh pr view` / `gh pr list` |

## Dokumentasi API

> **ATURAN MUTLAK:** Endpoint tanpa dokumentasi lengkap **TIDAK BOLEH** di-commit.
> AI **WAJIB** melengkapi dokumentasi sebelum menyelesaikan implementasi endpoint.

- FastAPI secara otomatis menghasilkan Swagger UI di `/docs` dan ReDoc di `/redoc`.
- Setiap endpoint **WAJIB** memiliki keempat atribut berikut — tidak boleh ada yang dilewatkan:
  - `summary` — deskripsi singkat.
  - `description` — penjelasan lebih detail (markdown didukung).
  - `response_model` — schema Pydantic untuk response.
  - `responses` — definisi kode HTTP error yang mungkin dikembalikan.
- Semua Pydantic schema **WAJIB** memiliki `model_config` dengan `json_schema_extra` berisi contoh data nyata (bukan placeholder).

## Docker

> **ATURAN MUTLAK:** AI **WAJIB** memastikan image Docker aman dan tidak mengandung
> informasi sensitif sebelum melakukan build atau push.

### Dockerfile

**WAJIB** gunakan **multi-stage build**:
1. Stage `builder` — install dependensi.
2. Stage `runtime` — image final yang ringan (base image `python:3.11-slim`).

**DILARANG** menyertakan file test, `.env`, atau credential di image final.
**DILARANG** menggunakan `python:3.11` (non-slim) sebagai base image final — gunakan `python:3.11-slim`.

### Environment Variables

**WAJIB** simpan semua konfigurasi sensitif di environment variable.
**WAJIB** gunakan `.env.example` sebagai template untuk environment variables.
**DILARANG KERAS** commit file `.env` ke repository dalam kondisi apapun.

## Konvensi Penamaan

| Elemen | Konvensi | Contoh |
|---|---|---|
| File Python | snake_case | `cvi_calculator.py` |
| Class | PascalCase | `CVICalculator` |
| Fungsi/method | snake_case | `calculate_cvi()` |
| Variabel | snake_case | `expert_ratings` |
| Konstanta | UPPER_SNAKE_CASE | `MAX_EXPERTS` |
| Tabel DB | snake_case (plural) | `instruments`, `expert_ratings` |
| Kolom DB | snake_case | `created_at`, `item_id` |
| Endpoint URL | kebab-case | `/api/v1/cvi-calculations` |
