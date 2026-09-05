#!/usr/bin/env python
"""
Create an admin user in the database.
Usage: python scripts/create_admin.py --username <username> --password <password>
Or run without arguments for interactive mode.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path so we can import app module
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import AdminUser
from app.security import hash_password


def create_admin_interactive():
    """Interactive mode: prompt for username and password."""
    print("=== Create Admin User ===\n")
    
    username = input("Enter username: ").strip()
    if not username:
        print("Error: Username cannot be empty.")
        return False
    
    # Check if username already exists
    db = SessionLocal()
    existing = db.query(AdminUser).filter(AdminUser.username == username).first()
    if existing:
        print(f"Error: Username '{username}' already exists.")
        db.close()
        return False
    
    password = input("Enter password: ").strip()
    if not password:
        print("Error: Password cannot be empty.")
        db.close()
        return False
    
    confirm_password = input("Confirm password: ").strip()
    if password != confirm_password:
        print("Error: Passwords do not match.")
        db.close()
        return False
    
    # Hash and create
    password_hash = hash_password(password)
    admin = AdminUser(username=username, password_hash=password_hash)
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    
    print(f"\n✓ Admin user '{username}' created successfully!")
    print(f"  Admin ID: {admin.id}")
    return True


def create_admin_args(username: str, password: str):
    """Create admin from command-line arguments."""
    db = SessionLocal()
    
    # Check if username already exists
    existing = db.query(AdminUser).filter(AdminUser.username == username).first()
    if existing:
        print(f"Error: Username '{username}' already exists.")
        db.close()
        return False
    
    # Hash and create
    password_hash = hash_password(password)
    admin = AdminUser(username=username, password_hash=password_hash)
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    
    print(f"✓ Admin user '{username}' created successfully!")
    print(f"  Admin ID: {admin.id}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Create an admin user for the Freshers Party backend."
    )
    parser.add_argument("--username", type=str, help="Admin username")
    parser.add_argument("--password", type=str, help="Admin password")
    
    args = parser.parse_args()
    
    if args.username and args.password:
        # Command-line mode
        create_admin_args(args.username, args.password)
    else:
        # Interactive mode
        create_admin_interactive()


if __name__ == "__main__":
    main()
