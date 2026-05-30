from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Media(Base):
    __tablename__ = "media"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    destination_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("destinations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    journal_entry_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(2000), nullable=False)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    caption: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    destination: Mapped["Destination"] = relationship(
        "Destination",
        back_populates="media",
        foreign_keys=[destination_id],
    )
    journal_entry: Mapped["JournalEntry"] = relationship(
        "JournalEntry",
        back_populates="media",
        foreign_keys=[journal_entry_id],
    )
