"""Perluas kolom id di tabel users dari VARCHAR(36) ke VARCHAR(255).

Sub claim dari Authentik bisa lebih panjang dari 36 karakter (UUID).

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Ubah kolom users.id menjadi VARCHAR(255)."""
    op.alter_column(
        "users",
        "id",
        existing_type=sa.String(36),
        type_=sa.String(255),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Kembalikan kolom users.id ke VARCHAR(36)."""
    op.alter_column(
        "users",
        "id",
        existing_type=sa.String(255),
        type_=sa.String(36),
        existing_nullable=False,
    )
