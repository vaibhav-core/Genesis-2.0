from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event
from ..services.admin_service import pass_distribution_available
from ..services.student_service import find_student_by_roll, find_students_by_name
from ..schemas import PassVerifyRequest, PassVerifyResponseSuccess, PassVerifyResponseFailure


router = APIRouter(prefix="/api/pass", tags=["Pass"])


@router.post("/verify")
def verify_pass(
    request: PassVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify student identity by roll number or name.
    Returns 200 with valid/invalid status (never 404).
    """
    if request.event_id is not None:
        event = db.query(Event).filter(Event.id == request.event_id).first()
        if not event:
            return PassVerifyResponseFailure(valid=False, reason="event_not_found", message="Event not found.")
        if not pass_distribution_available(event):
            return PassVerifyResponseFailure(valid=False, reason="pass_distribution_not_open", message="Pass distribution is not open for this event.")

    if request.identifier_type == "roll_number":
        student = find_student_by_roll(request.value, db)
        
        if student:
            return PassVerifyResponseSuccess(
                valid=True,
                student={
                    "roll_number": student.roll_number,
                    "name": student.name
                }
            )
        else:
            return PassVerifyResponseFailure(
                valid=False,
                reason="student_not_found",
                message="Student not registered."
            )
    
    elif request.identifier_type == "name":
        students = find_students_by_name(request.value, db)
        
        if len(students) == 1:
            student = students[0]
            return PassVerifyResponseSuccess(
                valid=True,
                student={
                    "roll_number": student.roll_number,
                    "name": student.name
                }
            )
        elif len(students) > 1:
            return PassVerifyResponseFailure(
                valid=False,
                reason="multiple_students_found",
                message="Multiple students have this name. Please enter your roll number."
            )
        else:
            return PassVerifyResponseFailure(
                valid=False,
                reason="student_not_found",
                message="Student not registered."
            )
    
    else:
        return PassVerifyResponseFailure(
            valid=False,
            reason="invalid_request",
            message="identifier_type must be 'roll_number' or 'name'."
        )