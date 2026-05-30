"""Set cover_media_id to last uploaded media for destinations without a cover

Revision ID: 006_set_cover_images
Revises: 005_titlecase_seasons
Create Date: 2026-04-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_set_cover_images"
down_revision: Union[str, None] = "005_titlecase_seasons"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For every destination that has no cover image set, pick the most recently
    # uploaded media item (by upload_date) and assign it as the cover.
    op.execute("""
        UPDATE destinations d
        SET cover_media_id = sub.last_media_id
        FROM (
            SELECT DISTINCT ON (destination_id) destination_id, id AS last_media_id
            FROM media
            WHERE destination_id IS NOT NULL
            ORDER BY destination_id, upload_date DESC
        ) sub
        WHERE d.id = sub.destination_id
          AND d.cover_media_id IS NULL
    """)


def downgrade() -> None:
    # Cannot reliably revert — we don't know which were previously NULL
    pass
