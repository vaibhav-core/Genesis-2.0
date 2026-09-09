"""Voting logic for registered and free-identifier voters."""

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Candidate, Event, Vote
from ..schemas import VoteRequest, VotingVerifyRequest
from .student_service import find_student_by_roll, normalize_roll, verify_student_identity


def _event_and_candidate(event_id: int, candidate_id: int, db: Session):
    event = db.query(Event).filter(Event.id == event_id).first()
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.event_id == event_id,
        Candidate.active == True,
    ).first()
    return event, candidate


def _voter_details(request, db: Session):
    if request.mode == "free":
        return True, None, None, normalize_roll(request.voter_identifier)

    valid, student = verify_student_identity(request.roll_number, request.name, db)
    if not student:
        reason = "student_not_found" if not find_student_by_roll(request.roll_number, db) else "identity_mismatch"
        return False, reason, None, None
    if not student.eligible_to_vote:
        return False, "not_eligible", student, None
    return valid, None, student, None


def verify_vote_eligibility(request: VotingVerifyRequest, db: Session):
    event, candidate = _event_and_candidate(request.event_id, request.candidate_id, db)
    if not event or not event.voting_enabled:
        return False, "voting_not_enabled", None
    if event.voting_status != "open":
        return False, "voting_not_open", None
    if not candidate:
        return False, "invalid_candidate", None

    valid, reason, student, free_identifier = _voter_details(request, db)
    if not valid:
        return False, reason, student
    duplicate_filter = (
        Vote.voter_id == student.id
        if student else Vote.free_voter_identifier == free_identifier
    )
    duplicate = db.query(Vote).filter(
        Vote.event_id == request.event_id,
        duplicate_filter,
    ).first()
    if duplicate:
        return False, "already_voted", student
    return True, None, student


def submit_vote(request: VoteRequest, db: Session):
    event, candidate = _event_and_candidate(request.event_id, request.candidate_id, db)
    if not event or not event.voting_enabled:
        return False, "voting_not_enabled", "Voting is not enabled for this event."
    if event.voting_status != "open":
        return False, "voting_not_open", "Voting is not open for this event."
    if not candidate:
        return False, "invalid_candidate", "Candidate not found, inactive, or not in this event."

    valid, reason, student, free_identifier = _voter_details(request, db)
    if not valid:
        messages = {
            "student_not_found": "Student not registered.",
            "identity_mismatch": "Name does not match roll number.",
            "not_eligible": "You are not eligible to vote.",
        }
        return False, reason, messages.get(reason, "Validation failed.")

    duplicate_filter = (
        Vote.voter_id == student.id
        if student else Vote.free_voter_identifier == free_identifier
    )
    if db.query(Vote).filter(
        Vote.event_id == request.event_id,
        duplicate_filter,
    ).first():
        return False, "already_voted", "You have already voted in this event."

    vote = Vote(
        event_id=request.event_id,
        candidate_id=request.candidate_id,
        voter_id=student.id if student else None,
        free_voter_identifier=free_identifier,
    )
    try:
        db.add(vote)
        db.commit()
        return True, None, None
    except IntegrityError:
        db.rollback()
        return False, "already_voted", "You have already voted in this event."


def get_voting_results(event_id: int, db: Session) -> list[dict]:
    results = db.query(
        Candidate.id.label("candidate_id"),
        Candidate.name,
        func.count(Vote.id).label("votes"),
    ).join(Vote, Vote.candidate_id == Candidate.id).filter(
        Candidate.event_id == event_id,
        Candidate.active == True,
    ).group_by(Candidate.id, Candidate.name).order_by(func.count(Vote.id).desc()).all()
    return [{"candidate_id": row[0], "name": row[1], "votes": row[2]} for row in results]
