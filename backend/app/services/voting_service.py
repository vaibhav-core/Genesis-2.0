"""
Voting logic: vote submission, validation, and results.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ..models import Student, Candidate, Vote
from .student_service import verify_student_identity, find_student_by_roll


def verify_vote_eligibility(
    roll_number: str,
    name: str,
    category: str,
    db: Session
) -> tuple[bool, str | None, Student | None]:
    """
    Verify if a student can vote in a category.
    Returns (is_valid, reason_if_invalid, student).
    
    Possible reasons:
    - "student_not_found"
    - "identity_mismatch"
    - "not_eligible"
    - None (if valid)
    """
    # 1. Verify identity (roll number + name match)
    is_valid, student = verify_student_identity(roll_number, name, db)
    
    if not student:
        # Could be either not found or mismatch; check which
        if not find_student_by_roll(roll_number, db):
            return False, "student_not_found", None
        else:
            return False, "identity_mismatch", None
    
    # 2. Check eligibility
    if not student.eligible_to_vote:
        return False, "not_eligible", student
    
    # 3. Check if already voted in this category
    existing_vote = db.query(Vote).filter(
        Vote.voter_id == student.id,
        Vote.category == category
    ).first()
    
    if existing_vote:
        return False, "already_voted", student
    
    return True, None, student


def submit_vote(
    roll_number: str,
    name: str,
    candidate_id: int,
    category: str,
    db: Session
) -> tuple[bool, str | None, str | None]:
    """
    Submit a vote with full validation.
    Validation order (fail fast):
    1. Verify identity
    2. Verify eligibility
    3. Verify candidate exists and is active
    4. Verify category matches
    5. Check no duplicate vote (pre-check + DB constraint as fallback)
    6. Insert vote
    
    Returns (success, reason_if_failed, message_if_failed).
    
    Possible reasons on failure:
    - "student_not_found"
    - "identity_mismatch"
    - "not_eligible"
    - "invalid_candidate"
    - "already_voted"
    """
    
    # 1-2. Verify eligibility (includes identity check)
    is_valid, reason, student = verify_vote_eligibility(roll_number, name, category, db)
    if not is_valid:
        message = {
            "student_not_found": "Student not registered.",
            "identity_mismatch": "Name does not match roll number.",
            "not_eligible": "You are not eligible to vote.",
            "already_voted": "You have already voted in this category."
        }.get(reason, "Validation failed.")
        return False, reason, message
    
    # 3-4. Verify candidate
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate or not candidate.active:
        return False, "invalid_candidate", "Candidate not found or inactive."
    
    if candidate.category != category:
        return False, "invalid_candidate", "Candidate category does not match."
    
    # 5. Re-check no duplicate (paranoia)
    existing_vote = db.query(Vote).filter(
        Vote.voter_id == student.id,
        Vote.category == category
    ).first()
    
    if existing_vote:
        return False, "already_voted", "You have already voted in this category."
    
    # 6. Insert vote
    try:
        vote = Vote(
            voter_id=student.id,
            candidate_id=candidate_id,
            category=category
        )
        db.add(vote)
        db.commit()
        db.refresh(vote)
        return True, None, None
    except IntegrityError:
        # Race condition: another request inserted the vote between our check and insert
        db.rollback()
        return False, "already_voted", "You have already voted in this category."


def get_voting_results(category: str, db: Session) -> list[dict]:
    """
    Get voting results for a category.
    Returns list of dicts: [{"candidate_id": 1, "name": "Candidate A", "votes": 183}, ...]
    Sorted by votes descending.
    """
    results = db.query(
        Candidate.id.label("candidate_id"),
        Candidate.name,
        func.count(Vote.id).label("votes")
    ).join(
        Vote, Vote.candidate_id == Candidate.id
    ).filter(
        Candidate.category == category,
        Candidate.active == True
    ).group_by(
        Candidate.id,
        Candidate.name
    ).order_by(
        func.count(Vote.id).desc()
    ).all()
    
    return [
        {
            "candidate_id": r[0],
            "name": r[1],
            "votes": r[2]
        }
        for r in results
    ]
