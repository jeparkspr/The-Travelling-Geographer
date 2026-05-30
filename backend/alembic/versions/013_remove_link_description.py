"""Remove description column from links table

Revision ID: 013_remove_link_description
Revises: 012_add_sharing_tables
Create Date: 2026-05-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "013_remove_link_description"
down_revision: Union[str, None] = "012_add_sharing_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("links", "description")


def downgrade() -> None:
    op.add_column("links", sa.Column("description", sa.Text(), nullable=True))
