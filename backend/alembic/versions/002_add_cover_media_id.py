"""Add cover_media_id to destinations

Revision ID: 002_add_cover_media_id
Revises: 001_initial
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_add_cover_media_id"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "destinations",
        sa.Column("cover_media_id", postgresql.UUID(as_uuid=False), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("destinations", "cover_media_id")
