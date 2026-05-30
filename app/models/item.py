"""Model SQLAlchemy untuk entitas Item (butir instrumen)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Item(Base):
    """Model SQLAlchemy untuk tabel items.

    Merepresentasikan satu butir/pernyataan dalam sebuah instrumen CVI
    yang akan dinilai relevansinya oleh para expert.
    """

    __tablename__ = "items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    instrument_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Nomor urut item dalam instrumen",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Teks/pernyataan dari item ini",
    )
    domain: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Domain/dimensi opsional untuk pengelompokan item",
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
