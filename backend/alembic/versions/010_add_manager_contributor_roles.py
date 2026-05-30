"""Add Manager and Contributor system roles

Revision ID: 010_add_extra_roles
Revises: 009_add_auth_tables
Create Date: 2026-05-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010_add_extra_roles"
down_revision: Union[str, None] = "009_add_auth_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO roles (name, default_tier, is_system, can_manage_users, can_manage_settings)
        VALUES
            ('Manager',     'manage',     true, true,  true),
            ('Contributor', 'contribute', true, false, false)
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM roles WHERE name IN ('Manager', 'Contributor') AND is_system = true")
