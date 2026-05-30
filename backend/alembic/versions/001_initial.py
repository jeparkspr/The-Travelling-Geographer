"""Initial database schema with PostGIS support

Revision ID: 001_initial
Revises:
Create Date: 2026-04-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create destinations table
    op.create_table(
        "destinations",
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), server_default="researching", nullable=False),
        sa.Column("date_added", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("date_researched", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_start_date", sa.Date(), nullable=True),
        sa.Column("planned_end_date", sa.Date(), nullable=True),
        sa.Column("visited_start_date", sa.Date(), nullable=True),
        sa.Column("visited_end_date", sa.Date(), nullable=True),
        sa.Column("country", sa.String(255), nullable=False),
        sa.Column("region", sa.String(255), nullable=True),
        sa.Column("city", sa.String(255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("location", Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("cost_estimate", sa.Numeric(10, 2), nullable=True),
        sa.Column("cost_actual", sa.Numeric(10, 2), nullable=True),
        sa.Column("priority", sa.String(50), nullable=True),
        sa.Column("best_season", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), server_default="{}",nullable=False),
        sa.Column("custom_field_values", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_destinations_name", "name"),
        sa.Index("ix_destinations_status", "status"),
        sa.Index("ix_destinations_country", "country"),
        sa.Index("ix_destinations_region", "region"),
        sa.Index("ix_destinations_city", "city"),
        sa.Index("ix_destinations_priority", "priority"),
        sa.Index("ix_destinations_tags_gin", "tags", postgresql_using="gin"),
        sa.Index("ix_destinations_location_gist", "location", postgresql_using="gist"),
    )

    # Create full-text search index using raw SQL (REGCONFIG type can't be rendered by SQLAlchemy DDL)
    op.execute(
        "CREATE INDEX ix_destinations_search_tsvector ON destinations "
        "USING gin (to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, '')))"
    )

    # Create links table
    op.create_table(
        "links",
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("destination_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("url", sa.String(2000), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_links_destination_id", "destination_id"),
    )

    # Create journal_entries table
    op.create_table(
        "journal_entries",
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("destination_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("entry_date", sa.Date(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_journal_entries_destination_id", "destination_id"),
    )

    # Create media table
    op.create_table(
        "media",
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("destination_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("journal_entry_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("file_path", sa.String(2000), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("caption", sa.String(1000), nullable=True),
        sa.Column("upload_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["journal_entries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_media_destination_id", "destination_id"),
        sa.Index("ix_media_journal_entry_id", "journal_entry_id"),
    )

    # Create custom_field_definitions table
    op.create_table(
        "custom_field_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("field_key", sa.String(255), nullable=False),
        sa.Column("field_type", sa.String(50), nullable=False),
        sa.Column("options", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("field_key"),
        sa.Index("ix_custom_field_definitions_field_name", "field_name"),
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_custom_field_definitions_field_name", table_name="custom_field_definitions")
    op.drop_index("ix_media_journal_entry_id", table_name="media")
    op.drop_index("ix_media_destination_id", table_name="media")
    op.drop_index("ix_journal_entries_destination_id", table_name="journal_entries")
    op.drop_index("ix_links_destination_id", table_name="links")
    op.drop_index("ix_destinations_location_gist", table_name="destinations")
    op.execute("DROP INDEX IF EXISTS ix_destinations_search_tsvector")
    op.drop_index("ix_destinations_tags_gin", table_name="destinations")
    op.drop_index("ix_destinations_priority", table_name="destinations")
    op.drop_index("ix_destinations_city", table_name="destinations")
    op.drop_index("ix_destinations_region", table_name="destinations")
    op.drop_index("ix_destinations_country", table_name="destinations")
    op.drop_index("ix_destinations_status", table_name="destinations")
    op.drop_index("ix_destinations_name", table_name="destinations")

    # Drop tables
    op.drop_table("custom_field_definitions")
    op.drop_table("media")
    op.drop_table("journal_entries")
    op.drop_table("links")
    op.drop_table("destinations")

    # Drop extensions
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS postgis")
