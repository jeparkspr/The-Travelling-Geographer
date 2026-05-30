"""Add auth tables: users, roles, user_roles, refresh_tokens + owner_id on destinations

Revision ID: 009_add_auth_tables
Revises: 008_remove_google_search_links
Create Date: 2026-05-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = "009_add_auth_tables"
down_revision: Union[str, None] = "008_remove_google_search_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Users ---
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("totp_secret", sa.String(255), nullable=True),
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("recovery_codes", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
    )

    # --- Roles ---
    op.create_table(
        "roles",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("default_tier", sa.String(20), nullable=False, server_default=sa.text("'view'")),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("can_manage_users", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("can_manage_settings", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # --- User ↔ Role join ---
    op.create_table(
        "user_roles",
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", UUID(as_uuid=False), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )

    # --- Refresh tokens ---
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- owner_id on destinations ---
    op.add_column("destinations", sa.Column("owner_id", UUID(as_uuid=False), nullable=True))
    op.create_index("ix_destinations_owner_id", "destinations", ["owner_id"])
    op.create_foreign_key(
        "fk_destinations_owner_id",
        "destinations",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- Seed system roles ---
    op.execute("""
        INSERT INTO roles (name, default_tier, is_system, can_manage_users, can_manage_settings)
        VALUES
            ('Administrator', 'manage', true, true,  true),
            ('User',          'edit',   true, false, false)
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_constraint("fk_destinations_owner_id", "destinations", type_="foreignkey")
    op.drop_index("ix_destinations_owner_id", table_name="destinations")
    op.drop_column("destinations", "owner_id")
    op.drop_table("refresh_tokens")
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("users")
