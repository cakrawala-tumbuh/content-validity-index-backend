"""Migrasi: perluas kolom user ID dari String(36) ke String(255).

Authentik menggunakan sub claim berupa 64-karakter hex string,
lebih panjang dari UUID standar (36 karakter).

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Perluas kolom user ID ke String(255)."""
    # users.id (PK) — perlu drop/recreate FK constraints terlebih dahulu
    with op.batch_alter_table("expert_assignments") as batch_op:
        batch_op.alter_column("user_id", type_=sa.String(255), existing_nullable=False)
        batch_op.alter_column("assigned_by", type_=sa.String(255), existing_nullable=False)

    with op.batch_alter_table("ratings") as batch_op:
        batch_op.alter_column("user_id", type_=sa.String(255), existing_nullable=False)

    with op.batch_alter_table("instruments") as batch_op:
        batch_op.alter_column("created_by", type_=sa.String(255), existing_nullable=False)

    with op.batch_alter_table("activity_logs") as batch_op:
        batch_op.alter_column("user_id", type_=sa.String(255), existing_nullable=True)

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("id", type_=sa.String(255), existing_nullable=False)


def downgrade() -> None:
    """Kembalikan kolom user ID ke String(36)."""
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("id", type_=sa.String(36), existing_nullable=False)

    with op.batch_alter_table("activity_logs") as batch_op:
        batch_op.alter_column("user_id", type_=sa.String(36), existing_nullable=True)

    with op.batch_alter_table("instruments") as batch_op:
        batch_op.alter_column("created_by", type_=sa.String(36), existing_nullable=False)

    with op.batch_alter_table("ratings") as batch_op:
        batch_op.alter_column("user_id", type_=sa.String(36), existing_nullable=False)

    with op.batch_alter_table("expert_assignments") as batch_op:
        batch_op.alter_column("user_id", type_=sa.String(36), existing_nullable=False)
        batch_op.alter_column("assigned_by", type_=sa.String(36), existing_nullable=False)
