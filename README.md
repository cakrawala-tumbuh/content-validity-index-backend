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
