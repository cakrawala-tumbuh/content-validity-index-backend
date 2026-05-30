"""Model SQLAlchemy untuk entitas Rating (penilaian expert)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Rating(Base):
    """Model SQLAlchemy untuk tabel ratings.

    Menyimpan penilaian relevansi seorang expert terhadap satu item
    dalam sebuah instrumen. Satu expert hanya bisa memberikan satu
    penilaian per item per assignment (UNIQUE constraint).

    Skala penilaian relevansi:
        1 = Tidak relevan
        2 = Kurang relevan
        3 = Cukup relevan (dianggap relevan untuk I-CVI)
        4 = Sangat relevan (dianggap relevan untuk I-CVI)
    """

    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("assignment_id", "item_id", name="uq_rating_assignment_item"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    assignment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("expert_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Denormalisasi untuk efisiensi query",
    )
    relevance_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Skor relevansi 1-4 (1=tidak relevan, 4=sangat relevan)",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Catatan opsional dari expert",
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
