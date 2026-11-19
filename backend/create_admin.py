"""Create the first admin account (use this in production instead of seed.py).

    python create_admin.py --email you@company.com --name "Your Name"
"""
import argparse
import getpass
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Platform Admin")
    parser.add_argument("--password", help="omit to be prompted securely")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Password (min 12 chars): ")
    if len(password) < 12 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password):
        sys.exit("Password must be at least 12 characters and contain letters and numbers.")

    db = SessionLocal()
    try:
        email = args.email.lower().strip()
        if db.scalar(select(User).where(User.email == email)):
            sys.exit(f"A user with email {email} already exists.")
        db.add(User(name=args.name, email=email, hashed_password=hash_password(password), role="admin"))
        db.commit()
        print(f"Admin {email} created.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
