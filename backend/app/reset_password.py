"""CLI tool to reset a user's password.

Usage (from the Docker host):
    docker exec -it tg-app python -m app.reset_password

Prompts for email and new password interactively.
"""

import asyncio
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.user import User
from app.services.auth import hash_password, validate_password


async def main():
    print("\n=== The Travelling Geographer — Password Reset ===\n")

    email = input("Email address: ").strip()
    if not email:
        print("No email entered. Aborting.")
        sys.exit(1)

    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None:
            print(f"No user found with email: {email}")
            sys.exit(1)

        print(f"Found user: {user.display_name} ({user.email})")

        password = getpass.getpass("New password: ")
        pwd_errors = validate_password(password)
        if pwd_errors:
            print("Password does not meet complexity requirements:")
            for err in pwd_errors:
                print(f"  - {err}")
            sys.exit(1)

        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match. Aborting.")
            sys.exit(1)

        user.password_hash = hash_password(password)
        await db.commit()

        print(f"\nPassword updated successfully for {user.display_name}.")


if __name__ == "__main__":
    asyncio.run(main())
