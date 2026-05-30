"""Remove Google Image Search links

Revision ID: 007_remove_google_images_links
Revises: 006_set_cover_images
Create Date: 2026-04-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007_remove_google_images_links"
down_revision: Union[str, None] = "006_set_cover_images"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DELETE FROM links
        WHERE url LIKE '%images.google.com%'
           OR title = 'Google Image Search'
           OR url LIKE 'https://www.google.com/search%'
    """)


def downgrade() -> None:
    # Cannot restore deleted links
    pass
