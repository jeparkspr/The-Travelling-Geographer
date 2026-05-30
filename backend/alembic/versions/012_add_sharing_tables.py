"""Add board_shares and destination_shares tables

Revision ID: 012_add_sharing_tables
Revises: 011_simplify_roles
Create Date: 2026-05-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "012_add_sharing_tables"
down_revision: Union[str, None] = "011_simplify_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Board shares — share all of a user's destinations with another user
    op.create_table(
        "board_shares",
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shared_with_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_tier", sa.String(20), nullable=False, server_default="view"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_board_shares_owner_id", "board_shares", ["owner_id"])
    op.create_index("ix_board_shares_shared_with_id", "board_shares", ["shared_with_id"])
    op.create_index("uq_board_shares_owner_shared", "board_shares", ["owner_id", "shared_with_id"], unique=True)

    # Destination shares — share a single destination with another user
    op.create_table(
        "destination_shares",
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("destination_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shared_with_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_tier", sa.String(20), nullable=False, server_default="view"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_destination_shares_destination_id", "destination_shares", ["destination_id"])
    op.create_index("ix_destination_shares_shared_with_id", "destination_shares", ["shared_with_id"])
    op.create_index("uq_dest_shares_dest_shared", "destination_shares", ["destination_id", "shared_with_id"], unique=True)


def downgrade() -> None:
    op.drop_table("destination_shares")
    op.drop_table("board_shares")
