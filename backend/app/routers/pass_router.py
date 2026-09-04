from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student


router = APIRouter(prefix="/api/pass", tags=["Pass"])


@router.post("/verify")
def verify_roll_number(
    roll_number: str,
    db: Session = Depends(get_db)
):
    # Normalize user input
    roll_number = roll_number.strip().upper()

    student = (
        db.query(Student)
        .filter(Student.roll_number == roll_number)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Roll number not registered"
        )

    return {
        "valid": True,
        "student": {
            "roll_number": student.roll_number,
            "name": student.name,
            "branch": student.branch,
            "year": student.year
        }
    }