"""Model SQLAlchemy untuk entitas Instrument (CVI project)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Instrument(Base):
    """Model SQLAlchemy untuk tabel instruments.

    Satu instrumen merepresentasikan satu CVI project yang berisi
    banyak item untuk dinilai oleh para expert.

    Status instrumen:
        - draft: Sedang dalam penyusunan, belum bisa dinilai.
        - active: Aktif dan terbuka untuk penilaian expert.
        - closed: Penilaian ditutup, hasil dapat dilihat.
    """

    __tablename__ = "instruments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        comment="Status: draft | active | closed",
    )
    created_by: Mapped[str | None] = mapped_column(
        String(255),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
