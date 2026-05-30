from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    String,
    Text,
    Float,
    Integer,
    Numeric,
    DateTime,
    Date,
    Boolean,
    ForeignKey,
    func,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.database import Base


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    owner_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="suggested",
        index=True,
    )
    date_added: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    date_researched: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    planned_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    planned_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    visited_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    visited_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    country: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
        index=True,
    )
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_estimate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    cost_actual: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    priority: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    cover_media_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
    )
    best_season: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=[], nullable=False)
    custom_field_values: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)
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
    owner: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[owner_id],
        lazy="selectin",
    )
    links: Mapped[List["Link"]] = relationship(
        "Link",
        back_populates="destination",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    media: Mapped[List["Media"]] = relationship(
        "Media",
        back_populates="destination",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="Media.destination_id",
    )
    journal_entries: Mapped[List["JournalEntry"]] = relationship(
        "JournalEntry",
        back_populates="destination",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    shares: Mapped[List["DestinationShare"]] = relationship(
        "DestinationShare",
        back_populates="destination",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_destinations_tags_gin", "tags", postgresql_using="gin"),
        Index(
            "ix_destinations_search_tsvector",
            func.to_tsvector("english", func.concat_ws(" ", name, description)),
            postgresql_using="gin",
        ),
        Index(
            "ix_destinations_location_gist",
            "location",
            postgresql_using="gist",
        ),
    )


class Link(Base):
    __tablename__ = "links"

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
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationship
    destination: Mapped["Destination"] = relationship(
        "Destination",
        back_populates="links",
    )
