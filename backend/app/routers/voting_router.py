from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Candidate
from ..services.student_service import verify_student_identity
from ..services.voting_service import verify_vote_eligibility, submit_vote, get_voting_results
from ..schemas import (
    CandidateResponse,
    VotingVerifyRequest,
    VotingVerifyResponseSuccess,
    VotingVerifyResponseFailure,
    VoteRequest,
    VoteResponseSuccess,
    VoteResponseFailure,
    VotingResultsResponse,
    VotingResultCandidate
)


router = APIRouter(prefix="/api/voting", tags=["Voting"])


@router.get("/candidates")
def get_candidates(db: Session = Depends(get_db)):
    """
    Get all active candidates.
    Returns list of candidates (only active=true).
    """
    candidates = db.query(Candidate).filter(Candidate.active == True).all()
    
    return [
        CandidateResponse(
            id=c.id,
            name=c.name,
            category=c.category,
            photo=c.photo,
            active=c.active
        )
        for c in candidates
    ]


@router.post("/verify")
def verify_voting(
    request: VotingVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify if a student can vote in a category.
    Returns 200 with valid/invalid status.
    """
    is_valid, reason, student = verify_vote_eligibility(
        request.roll_number,
        request.name,
        request.category,
        db
    )
    
    if is_valid:
        return VotingVerifyResponseSuccess(
            valid=True,
            already_voted=False
        )
    else:
        message = {
            "student_not_found": "Student not registered.",
            "identity_mismatch": "Name does not match roll number.",
            "not_eligible": "You are not eligible to vote.",
            "already_voted": "You have already voted in this category."
        }.get(reason, "Validation failed.")
        
        return VotingVerifyResponseFailure(
            valid=False,
            reason=reason,
            message=message
        )


@router.post("/vote")
def submit_voting(
    request: VoteRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a vote.
    Returns 200 with success/failure status (business-logic errors, not HTTP errors).
    """
    success, reason, message = submit_vote(
        request.roll_number,
        request.name,
        request.candidate_id,
        request.category,
        db
    )
    
    if success:
        return VoteResponseSuccess(success=True)
    else:
        return VoteResponseFailure(
            success=False,
            reason=reason,
            message=message or "Vote submission failed."
        )


@router.get("/results")
def get_results(category: str = Query(...), db: Session = Depends(get_db)):
    """
    Get voting results for a category.
    Results sorted by votes descending.
    """
    results = get_voting_results(category, db)
    
    return VotingResultsResponse(
        category=category,
        results=[
            VotingResultCandidate(**r)
            for r in results
        ]
    )
