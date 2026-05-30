"""Model SQLAlchemy untuk entitas ActivityLog (log aktivitas)."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ActivityLog(Base):
    """Model SQLAlchemy untuk tabel activity_logs.

    Menyimpan rekam jejak semua aktivitas pengguna dalam sistem,
    termasuk login, CRUD instrumen/item, assign expert,
    submit rating, kalkulasi CVI, dan ekspor.
    """

    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Nama aksi: login, create_instrument, submit_rating, dll.",
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Tipe resource yang dioperasikan: instrument, item, rating, dll.",
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="ID resource yang dioperasikan",
    )
    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        default="unknown",
    )
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        comment="Informasi tambahan dalam format JSON",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )
