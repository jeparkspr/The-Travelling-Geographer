from datetime import datetime

from sqlalchemy import String, Text, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

DEFAULT_AI_PROMPT = """Provide travel information about {location_name} in {country} (coordinates: {latitude}, {longitude}).

Write a description of 4 sections each with a paragraph being 2-3 sentences. Prior to each paragraph add a heading of Overview, Safety, Food, and Best Time to Visit. Separate headings and paragraphs with a blank line. Cover: key reasons to visit including landmarks and points of interest, cultural significance, brief history, a safety assessment, and food options. Also include specific recommendations on the best months to visit, what to expect in those months, and why those times are preferable — favoring periods that avoid peak tourist crowds while still offering good weather and experiences.

Suggest up to 3 descriptive tags that capture the most distinctive qualities of this destination.

For best seasons, select 1-4 from: Spring, Summer, Fall, Winter — prioritizing seasons that balance good conditions with fewer tourists.

Respond ONLY with valid JSON in this exact format:
{{
  "name": "Destination Name",
  "country": "Country",
  "region": "Continent or Region",
  "city": "Nearest City",
  "description": "Paragraph 1 (2-3 sentences). Paragraph 2 (2-3 sentences). Optional paragraph 3 (2-3 sentences).",
  "tags": ["tag1", "tag2", "tag3"],
  "best_season": ["Spring", "Fall"]
}}"""


class AppSetting(Base):
    __tablename__ = "app_settings"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
