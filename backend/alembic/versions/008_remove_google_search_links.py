"""Remove links with Google Search URLs

Revision ID: 008_remove_google_search_links
Revises: 007_remove_google_images_links
Create Date: 2026-04-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008_remove_google_search_links"
down_revision: Union[str, None] = "007_remove_google_images_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DELETE FROM links
        WHERE url LIKE 'https://www.google.com/search%'
    """)


def downgrade() -> None:
    # Cannot restore deleted links
    pass
