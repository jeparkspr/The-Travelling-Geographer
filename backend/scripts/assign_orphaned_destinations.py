"""
One-time script: Assign all orphaned destinations (owner_id IS NULL)
to the administrator account (john@circuitrunnings.com).

Usage (run inside the tg-app container):
    python scripts/assign_orphaned_destinations.py

Or from the host via docker exec:
    docker exec tg-app python scripts/assign_orphaned_destinations.py
"""

import asyncio
import os
import sys

# Allow running from the backend/ directory or from scripts/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, update, func
from app.database import async_session_maker
from app.models.user import User
from app.models.destination import Destination

ADMIN_EMAIL = "john@circuitrunnings.com"


async def main():
    async with async_session_maker() as db:
        # Find the admin user
        result = await db.execute(
            select(User).where(User.email == ADMIN_EMAIL)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            print(f"ERROR: No user found with email {ADMIN_EMAIL}")
            sys.exit(1)

        print(f"Found admin: {admin.display_name} (id={admin.id})")

        # Count orphaned destinations
        count_result = await db.execute(
            select(func.count()).select_from(Destination).where(
                Destination.owner_id.is_(None)
            )
        )
        orphan_count = count_result.scalar()

        if orphan_count == 0:
            print("No orphaned destinations found. Nothing to do.")
            return

        print(f"Found {orphan_count} orphaned destination(s). Assigning to {admin.display_name}...")

        # Update them
        await db.execute(
            update(Destination)
            .where(Destination.owner_id.is_(None))
            .values(owner_id=admin.id)
        )
        await db.commit()

        print(f"Done. {orphan_count} destination(s) assigned to {admin.display_name}.")


if __name__ == "__main__":
    asyncio.run(main())
