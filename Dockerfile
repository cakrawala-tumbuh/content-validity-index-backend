# Stage 1: builder — install dependensi ke direktori /install
FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install .


# Stage 2: runtime — image final yang ringan
FROM python:3.11-slim AS runtime

WORKDIR /app

# Salin dependensi dari stage builder
COPY --from=builder /install /usr/local

# Salin source code aplikasi
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Instal curl untuk healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Buat direktori data untuk file SQLite
RUN mkdir -p /data

# Jangan jalankan sebagai root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app /data
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
