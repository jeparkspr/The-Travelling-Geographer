"""
One-time script: Update the Boss user's email address.

Usage (run inside the tg-app container):
    python scripts/update_boss_email.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.database import async_session_maker
from app.models.user import User

OLD_EMAIL = "john@circuitrunnings.com"
NEW_EMAIL = "jeparkspr@gmail.com"


async def main():
    async with async_session_maker() as db:
        result = await db.execute(
            select(User).where(User.email == OLD_EMAIL)
        )
        user = result.scalar_one_or_none()

        if not user:
            print(f"ERROR: No user found with email {OLD_EMAIL}")
            sys.exit(1)

        print(f"Found user: {user.display_name} (id={user.id}, email={user.email})")
        user.email = NEW_EMAIL
        await db.commit()
        print(f"Done. Email updated to {NEW_EMAIL}")


if __name__ == "__main__":
    asyncio.run(main())
