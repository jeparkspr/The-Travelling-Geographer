"""Title-case best_season values

Revision ID: 005_titlecase_seasons
Revises: 004_add_app_settings
Create Date: 2026-04-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_titlecase_seasons"
down_revision: Union[str, None] = "004_add_app_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Replace lowercase season values with title-case in the best_season array column
    op.execute("""
        UPDATE destinations
        SET best_season = (
            SELECT array_agg(initcap(s))
            FROM unnest(best_season) AS s
        )
        WHERE best_season IS NOT NULL
    """)

    # Update the saved AI prompt template to use title-case seasons
    op.execute("""
        UPDATE app_settings
        SET value = replace(
            replace(
                replace(
                    replace(value, '"spring"', '"Spring"'),
                    '"summer"', '"Summer"'),
                '"fall"', '"Fall"'),
            '"winter"', '"Winter"')
        WHERE key = 'ai_prompt_template'
          AND value IS NOT NULL
    """)
    op.execute("""
        UPDATE app_settings
        SET value = replace(value,
            'select 1-4 from: spring, summer, fall, winter',
            'select 1-4 from: Spring, Summer, Fall, Winter')
        WHERE key = 'ai_prompt_template'
          AND value IS NOT NULL
    """)


def downgrade() -> None:
    # Revert title-case back to lowercase
    op.execute("""
        UPDATE destinations
        SET best_season = (
            SELECT array_agg(lower(s))
            FROM unnest(best_season) AS s
        )
        WHERE best_season IS NOT NULL
    """)
