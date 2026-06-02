# Content Validity Index Backend

Backend REST API berbasis **FastAPI** untuk pengelolaan **Content Validity Index (CVI)**.

## Tech Stack

- **FastAPI** — web framework async
- **SQLAlchemy 2.x + aiosqlite** — ORM dengan SQLite
- **Alembic** — migrasi database
- **Pydantic v2** — validasi data
- **Authentik** — identity provider (OIDC/JWT)
- **Docker** — containerization

## Menjalankan Aplikasi

```bash
cp .env.example .env
# Edit .env sesuai konfigurasi Authentik Anda

docker compose up
```

API tersedia di `http://localhost:8000`. Dokumentasi Swagger: `http://localhost:8000/docs`.

## Menjalankan Test

```bash
docker build -t cvi-backend:test .
docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test
```

---

## Panduan Akses & Modifikasi Data via API

### 1. Autentikasi

Semua endpoint (kecuali `/health`) memerlukan **JWT Bearer token** dari Authentik.

#### ⚠️ Keterbatasan Grant Type Authentik

> **Penting:** Tidak semua OAuth2 grant type bekerja dengan baik untuk mendapatkan token
> yang dikenali sebagai role `admin` oleh backend. Berikut ringkasan hasil uji:

| Grant Type | Hasil | Keterangan |
|---|---|---|
| `password` | ❌ Gagal | Authentik mengembalikan `invalid_grant` secara default. Harus diaktifkan secara eksplisit di pengaturan provider. |
| `client_credentials` | ⚠️ Terbatas | Token berhasil didapat, tetapi claim `groups` **selalu kosong** (`[]`). Backend tidak dapat menentukan role, sehingga semua request dianggap role `expert`. |
| `authorization_code` + PKCE | ✅ Bekerja | Token mengandung claim `groups` yang lengkap. **Ini satu-satunya cara yang menghasilkan token dengan role `admin`.** |

#### Mendapatkan Token via Authorization Code Flow (Direkomendasikan)

Untuk keperluan scripting/otomasi, gunakan Python dengan `requests` yang mensimulasikan
browser login ke Authentik, lalu melakukan auth code exchange dengan PKCE:

```bash
pip install requests
```

```python
import requests, hashlib, base64, os, re
from urllib.parse import urlencode, urlparse, parse_qs

BASE        = "https://<AUTHENTIK_HOST>"
CLIENT_ID   = "<CLIENT_ID>"
CLIENT_SECRET = "<CLIENT_SECRET>"
REDIRECT_URI  = "<NEXTAUTH_URL>/api/auth/callback/authentik"
APP_SLUG      = "<APP_SLUG>"   # contoh: ypii-cvi

s = requests.Session()
s.headers.update({"Accept": "application/json"})

# 1. Login ke Authentik (form-based)
flow_resp = s.get(f"{BASE}/api/v3/flows/executor/default-authentication-flow/?format=json")
flow_data = flow_resp.json()
flow_id   = flow_data["flow"]["slug"]
s.post(
    f"{BASE}/api/v3/flows/executor/{flow_id}/",
    json={"component": "ak-stage-identification", "uid_field": "<USERNAME>"},
)
s.post(
    f"{BASE}/api/v3/flows/executor/{flow_id}/",
    json={"component": "ak-stage-password", "password": "<PASSWORD>"},
)

# 2. Authorization Code + PKCE
verifier   = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()
challenge  = base64.urlsafe_b64encode(
    hashlib.sha256(verifier.encode()).digest()
).rstrip(b"=").decode()
state      = base64.urlsafe_b64encode(os.urandom(16)).rstrip(b"=").decode()

auth_resp = s.get(
    f"{BASE}/application/o/authorize/",
    params={
        "response_type": "code",
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "scope":         "openid email profile groups offline_access",
        "state":         state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    },
    allow_redirects=True,
)
# Ekstrak authorization code dari URL redirect
code = parse_qs(urlparse(auth_resp.url).query).get("code", [None])[0]

# 3. Tukar code dengan token
token_resp = s.post(
    f"{BASE}/application/o/token/",
    data={
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code_verifier": verifier,
    },
)
token = token_resp.json()["access_token"]
print(token)
```

#### Menggunakan Token

Gunakan `access_token` dari respons di setiap request:

```
Authorization: Bearer <access_token>
```

> **Catatan:** Access token Authentik biasanya berlaku **1 jam**. Jika token expired, ulangi
> langkah di atas atau gunakan `refresh_token` (jika scope `offline_access` diminta).

**Sinkronisasi setelah login (wajib saat pertama kali):**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/sync" \
  -H "Authorization: Bearer <token>"
```

---

### 2. Role & Hak Akses

| Role | Keanggotaan Group Authentik | Hak Akses |
|---|---|---|
| `admin` | `cvi-admin` (lihat `AUTHENTIK_ADMIN_GROUP`) | Akses penuh ke semua endpoint |
| `expert` | `cvi-expert` (lihat `AUTHENTIK_EXPERT_GROUP`) | Hanya instrumen yang di-assign dan rating milik sendiri |

---

### 3. Referensi Endpoint

Base URL: `http://localhost:8000/api/v1`

#### Auth

| Method | Endpoint | Role | Deskripsi |
|---|---|---|---|
| `POST` | `/auth/sync` | Semua | Sinkronisasi data user dari JWT Authentik ke DB lokal |

#### Users

| Method | Endpoint | Role | Deskripsi |
|---|---|---|---|
| `GET` | `/users/me` | Semua | Profil pengguna yang sedang login |
| `GET` | `/users/` | Admin | Daftar semua pengguna |
| `GET` | `/users/{user_id}` | Admin | Detail pengguna berdasarkan ID |
| `PATCH` | `/users/{user_id}` | Admin | Perbarui profil pengguna (termasuk `is_active`) |
| `DELETE` | `/users/{user_id}` | Admin | Nonaktifkan akun pengguna (soft delete) |

#### Instruments

| Method | Endpoint | Role | Deskripsi |
|---|---|---|---|
| `GET` | `/instruments/` | Semua | Daftar instrumen (admin: semua; expert: hanya yang di-assign) |
| `POST` | `/instruments/` | Admin | Buat instrumen baru |
| `GET` | `/instruments/{id}` | Semua | Detail instrumen |
| `PATCH` | `/instruments/{id}` | Admin | Perbarui instrumen |
| `DELETE` | `/instruments/{id}` | Admin | Hapus instrumen beserta item & assignment |

#### Items (dalam instrumen)

| Method | Endpoint | Role | Deskripsi |
|---|---|---|---|
| `GET` | `/instruments/{id}/items` | Semua | Daftar item dalam instrumen |
| `POST` | `/instruments/{id}/items` | Admin | Tambah satu item |
| `POST` | `/instruments/{id}/items/bulk` | Admin | Tambah banyak item sekaligus |
| `PATCH` | `/instruments/{id}/items/{item_id}` | Admin | Perbarui item |
| `DELETE` | `/instruments/{id}/items/{item_id}` | Admin | Hapus item |

#### Domains (dalam instrumen)

| Method | Endpoint | Role | Deskripsi |
|---|---|---|---|
| `GET` | `/instruments/{id}/domains` | Semua | Daftar domain/dimensi instrumen |
| `POST` | `/instruments/{id}/domains` | Admin | Tambah domain baru |
| `PATCH` | `/instruments/{id}/domains/{domain_id}` | Admin | Perbarui domain |
| `DELETE` | `/instruments/{id}/domains/{domain_id}` | Admin | Hapus domain |

#### Expert Assignments

| Method | Endpoint | Role | Deskripsi |
|---|---|---|---|
| `GET` | `/instruments/{id}/assignments` | Admin | Daftar expert yang di-assign ke instrumen |
| `POST` | `/instruments/{id}/assignments` | Admin | Assign expert ke instrumen |
| `DELETE` | `/instruments/{id}/assignments/{assignment_id}` | Admin | Batalkan assignment |

#### Ratings (Penilaian Expert)

| Method | Endpoint | Role | Deskripsi |
|---|---|---|---|
| `GET` | `/my-assignments` | Expert/Admin | Daftar instrumen yang di-assign ke user login |
| `GET` | `/assignments/{assignment_id}/ratings` | Expert/Admin | Daftar rating dalam assignment |
| `POST` | `/assignments/{assignment_id}/ratings/bulk` | Expert | Submit penilaian massal (upsert) |
| `PATCH` | `/assignments/{assignment_id}/ratings/{rating_id}` | Expert | Perbarui satu penilaian |

#### CVI Calculation

| Method | Endpoint | Role | Deskripsi |
|---|---|---|---|
| `GET` | `/instruments/{id}/cvi` | Admin | Hasil kalkulasi I-CVI, S-CVI/Ave, S-CVI/UA |
| `GET` | `/instruments/{id}/cvi/export` | Admin | Unduh hasil CVI dalam format Excel (.xlsx) |

#### Activity Logs

| Method | Endpoint | Role | Deskripsi |
|---|---|---|---|
| `GET` | `/activity-logs/` | Admin | Log aktivitas semua pengguna (dapat difilter) |

---

### 4. Contoh Request

**Membuat instrumen (admin):**

```bash
curl -X POST "http://localhost:8000/api/v1/instruments/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Instrumen Kuesioner A",
    "description": "Deskripsi instrumen",
    "version": "1.0"
  }'
```

**Menambah item secara bulk (admin):**

```bash
curl -X POST "http://localhost:8000/api/v1/instruments/<instrument_id>/items/bulk" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"content": "Item pertanyaan 1", "sequence_number": 1},
      {"content": "Item pertanyaan 2", "sequence_number": 2}
    ]
  }'
```

**Assign expert ke instrumen (admin):**

```bash
curl -X POST "http://localhost:8000/api/v1/instruments/<instrument_id>/assignments" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "<expert_user_id>",
    "deadline": "2025-12-31T23:59:59"
  }'
```

**Submit penilaian massal (expert):**

```bash
curl -X POST "http://localhost:8000/api/v1/assignments/<assignment_id>/ratings/bulk" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "ratings": [
      {"item_id": "<item_id_1>", "relevance_score": 4, "notes": "Sangat relevan"},
      {"item_id": "<item_id_2>", "relevance_score": 3, "notes": "Cukup relevan"}
    ]
  }'
```

> Skala penilaian: **1** (tidak relevan) — **2** (kurang relevan) — **3** (cukup relevan) — **4** (sangat relevan).
> Item dengan skor **3 atau 4** dihitung sebagai relevan dalam kalkulasi I-CVI.

**Melihat hasil kalkulasi CVI (admin):**

```bash
curl "http://localhost:8000/api/v1/instruments/<instrument_id>/cvi" \
  -H "Authorization: Bearer <token>"
```

**Mengunduh hasil CVI ke Excel (admin):**

```bash
curl "http://localhost:8000/api/v1/instruments/<instrument_id>/cvi/export" \
  -H "Authorization: Bearer <token>" \
  -o hasil_cvi.xlsx
```

**Melihat log aktivitas dengan filter (admin):**

```bash
curl "http://localhost:8000/api/v1/activity-logs/?action=login&limit=20" \
  -H "Authorization: Bearer <token>"
```

---

### 5. Kode Error Umum

| Kode | Arti | Penyebab Umum |
|---|---|---|
| `401` | Unauthorized | Token tidak ada, tidak valid, atau sudah kedaluwarsa |
| `403` | Forbidden | Token valid, tapi role tidak mencukupi atau akun nonaktif |
| `404` | Not Found | Resource (instrumen, item, user, dll.) tidak ditemukan |
| `400` | Bad Request | Data tidak valid (mis. expert sudah di-assign, skor di luar range) |
| `422` | Unprocessable Entity | Validasi Pydantic gagal (field wajib kosong, tipe data salah) |
| `429` | Too Many Requests | Rate limit terlampaui (default: 200 request/menit per IP) |
| `503` | Service Unavailable | Identity provider (Authentik) tidak dapat dihubungi |

---

### 6. Eksplorasi Interaktif

Gunakan Swagger UI untuk mencoba endpoint secara langsung di browser:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

Klik tombol **Authorize** di Swagger UI, masukkan token Bearer, lalu coba endpoint langsung dari browser.
