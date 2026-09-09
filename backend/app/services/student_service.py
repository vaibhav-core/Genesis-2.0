"""
Student lookup and matching logic.
Single source of truth for all normalization and name/roll matching.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import Student


# ============================================================================
# Canonical Normalization Rules (Part 1/8 spec)
# ============================================================================

def normalize_roll(roll_number: str) -> str:
    """Normalize roll number: strip whitespace and uppercase."""
    return roll_number.strip().upper()


def normalize_name(name: str) -> str:
    """Normalize name: strip whitespace only."""
    return name.strip()


def names_match(a: str, b: str) -> bool:
    """
    Case-insensitive name comparison.
    Both names are normalized and compared case-insensitively.
    """
    return normalize_name(a).casefold() == normalize_name(b).casefold()


# ============================================================================
# Student Lookup Functions
# ============================================================================

def find_student_by_roll(roll_number: str, db: Session) -> Student | None:
    """
    Find a student by roll number (exact match after normalization).
    Returns Student or None.
    """
    normalized_roll = normalize_roll(roll_number)
    return db.query(Student).filter(
        Student.roll_number == normalized_roll
    ).first()


def find_students_by_name(name: str, db: Session) -> list[Student]:
    """
    Find all students matching the name (case-insensitive after normalization).
    Returns list of Student objects.
    """
    normalized_name = normalize_name(name)
    
    # SQLite-safe case-insensitive query using func.lower()
    return db.query(Student).filter(
        func.lower(Student.name) == func.lower(normalized_name)
    ).all()


def verify_student_identity(roll_number: str, name: str, db: Session) -> tuple[bool, Student | None]:
    """
    Verify student identity: roll number resolves to a student AND name matches.
    Returns (is_valid, student).
    """
    student = find_student_by_roll(roll_number, db)
    
    if not student:
        return False, None
    
    if not names_match(name, student.name):
        return False, None
    
    return True, student
