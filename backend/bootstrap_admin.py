#!/usr/bin/env python
"""Promote an existing user to platform administrator.

Usage:
    python bootstrap_admin.py --email admin@example.com
"""

import argparse
from pathlib import Path
import sys

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv(Path(__file__).parent / ".env")

from database.connection import get_db
from services.auth_service import promote_user_to_admin


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote an existing Melo-AI user to platform admin")
    parser.add_argument("--email", required=True, help="Email address of the existing user to promote")
    args = parser.parse_args()

    db = next(get_db())
    try:
        user = promote_user_to_admin(db, args.email.strip().lower())
    finally:
        db.close()

    if user is None:
        print(f"No user found for {args.email}", file=sys.stderr)
        return 1

    print(f"Platform admin enabled for {user.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())