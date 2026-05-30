from datetime import datetime

from sqlalchemy import String, Integer, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CustomFieldDefinition(Base):
    __tablename__ = "custom_field_definitions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    field_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    field_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)
    options: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
