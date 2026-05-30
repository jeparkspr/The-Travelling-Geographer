"""Rename status 'noted' to 'suggested'

Revision ID: 003_rename_noted_to_suggested
Revises: 002_add_cover_media_id
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_rename_noted_to_suggested"
down_revision: Union[str, None] = "002_add_cover_media_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE destinations SET status = 'suggested' WHERE status = 'noted'")


def downgrade() -> None:
    op.execute("UPDATE destinations SET status = 'noted' WHERE status = 'suggested'")
