"""Simplify roles to Administrator and User only

Revision ID: 011_simplify_roles
Revises: 010_add_extra_roles
Create Date: 2026-05-05 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "011_simplify_roles"
down_revision: Union[str, None] = "010_add_extra_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rename "Admin" → "Administrator"
    op.execute("UPDATE roles SET name = 'Administrator' WHERE name = 'Admin'")

    # 2. Ensure "User" role exists
    op.execute("""
        INSERT INTO roles (name, default_tier, is_system, can_manage_users, can_manage_settings)
        VALUES ('User', 'edit', true, false, false)
        ON CONFLICT (name) DO NOTHING
    """)

    # 3. Reassign anyone on old roles (Manager, Editor, Contributor, Viewer) to "User"
    op.execute("""
        UPDATE user_roles
        SET role_id = (SELECT id FROM roles WHERE name = 'User')
        WHERE role_id IN (
            SELECT id FROM roles WHERE name IN ('Manager', 'Editor', 'Contributor', 'Viewer')
        )
    """)

    # 4. Delete the old roles
    op.execute("DELETE FROM roles WHERE name IN ('Manager', 'Editor', 'Contributor', 'Viewer')")


def downgrade() -> None:
    # Rename back
    op.execute("UPDATE roles SET name = 'Admin' WHERE name = 'Administrator'")
    # Re-create the old roles
    op.execute("""
        INSERT INTO roles (name, default_tier, is_system, can_manage_users, can_manage_settings)
        VALUES
            ('Manager',     'manage',     true, true,  true),
            ('Editor',      'edit',       true, false, false),
            ('Contributor', 'contribute', true, false, false),
            ('Viewer',      'view',       true, false, false)
        ON CONFLICT (name) DO NOTHING
    """)
