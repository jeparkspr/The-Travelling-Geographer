from datetime import datetime, date
from typing import List

from sqlalchemy import String, Text, Integer, DateTime, Date, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    destination_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("destinations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    destination: Mapped["Destination"] = relationship(
        "Destination",
        back_populates="journal_entries",
    )
    media: Mapped[List["Media"]] = relationship(
        "Media",
        back_populates="journal_entry",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="Media.journal_entry_id",
    )
