#!/usr/bin/env python
"""
Import students from a CSV file into the database.
Usage: python scripts/import_students.py path/to/students.csv

CSV Header Variants (case/space-insensitive):
  - Roll: "Roll Number", "roll_number", "Roll No", "roll no", "Roll", etc.
  - Name: "Name", "name", "Student Name", "student name", etc.
  
Optional columns:
  - Branch: "Branch", "branch", "Department", "dept", etc.
  - Year: "Year", "year", "Semester", "sem", etc.

Behavior:
- Skips rows with missing/empty roll number or name
- Skips rows with duplicate roll numbers (idempotent)
- Normalizes roll numbers (uppercase, stripped)
- Prints summary at end: Imported, Skipped (duplicate), Skipped (invalid)
"""

import sys
import csv
import argparse
from pathlib import Path

# Add parent directory to path so we can import app module
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Student
from app.services.student_service import normalize_roll, normalize_name


def normalize_header(header: str) -> str:
    """
    Normalize a CSV header for flexible matching.
    Removes spaces, converts to lowercase.
    """
    return header.strip().lower().replace(" ", "").replace("_", "")


def find_column_index(headers: list[str], possible_names: list[str]) -> int | None:
    """
    Find the index of a column by matching against possible normalized names.
    Returns None if no match found.
    """
    normalized_headers = [normalize_header(h) for h in headers]
    normalized_targets = [normalize_header(name) for name in possible_names]
    
    for i, normalized_header in enumerate(normalized_headers):
        if normalized_header in normalized_targets:
            return i
    
    return None


def import_students(csv_path: str, session_factory=SessionLocal):
    """
    Import students from CSV file.
    """
    csv_file = Path(csv_path)
    
    if not csv_file.exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    
    if not csv_file.suffix.lower() == ".csv":
        print(f"Error: File must be a CSV file: {csv_path}")
        sys.exit(1)
    
    # Open and read CSV
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
    except StopIteration:
        print("Error: CSV file is empty or has no header row")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    # Find column indices
    roll_index = find_column_index(headers, ["Roll Number", "Roll No", "Roll", "roll_number"])
    name_index = find_column_index(headers, ["Name", "Student Name"])
    branch_index = find_column_index(headers, ["Branch", "Department", "Dept"])
    year_index = find_column_index(headers, ["Year", "Semester", "Sem"])
    
    # Validate required columns
    if roll_index is None:
        print("Error: Could not find roll number column.")
        print(f"  Possible names: Roll Number, Roll No, Roll, roll_number")
        print(f"  Headers found: {', '.join(headers)}")
        sys.exit(1)
    
    if name_index is None:
        print("Error: Could not find name column.")
        print(f"  Possible names: Name, Student Name")
        print(f"  Headers found: {', '.join(headers)}")
        sys.exit(1)
    
    # Import students
    db = session_factory()
    imported = 0
    skipped_duplicate = 0
    skipped_invalid = 0
    
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
                # Extract fields
                roll = row[roll_index].strip() if roll_index < len(row) else ""
                name = row[name_index].strip() if name_index < len(row) else ""
                branch = row[branch_index].strip() if branch_index and branch_index < len(row) else None
                year_str = row[year_index].strip() if year_index and year_index < len(row) else None
                
                # Validate required fields
                if not roll or not name:
                    skipped_invalid += 1
                    continue
                
                # Normalize
                normalized_roll = normalize_roll(roll)
                normalized_name = normalize_name(name)
                
                # Parse year (optional)
                year = None
                if year_str:
                    try:
                        year = int(year_str)
                    except ValueError:
                        pass  # Ignore if not a valid integer
                
                # Check for duplicates
                existing = db.query(Student).filter(
                    Student.roll_number == normalized_roll
                ).first()
                
                if existing:
                    skipped_duplicate += 1
                    continue
                
                # Create student
                student = Student(
                    roll_number=normalized_roll,
                    name=normalized_name,
                    branch=branch if branch else None,
                    year=year,
                    eligible_to_vote=True
                )
                db.add(student)
                imported += 1
        
        # Commit all at once
        db.commit()
    
    except Exception as e:
        db.rollback()
        print(f"Error during import: {e}")
        sys.exit(1)
    finally:
        db.close()
    
    # Print summary
    print("\n" + "=" * 60)
    print("Import Summary")
    print("=" * 60)
    print(f"Imported:              {imported}")
    print(f"Skipped (duplicate):   {skipped_duplicate}")
    print(f"Skipped (invalid):     {skipped_invalid}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Import students from a CSV file into the database."
    )
    parser.add_argument("csv_path", type=str, help="Path to the CSV file")
    
    args = parser.parse_args()
    import_students(args.csv_path)


if __name__ == "__main__":
    main()
