"""
Admin service: candidates, events, and vote management.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models import Candidate, Event, Vote, Student


def create_candidate(name: str, category: str, photo: str | None, db: Session) -> Candidate:
    """Create a new candidate."""
    candidate = Candidate(
        name=name,
        category=category,
        photo=photo,
        active=True
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def update_candidate(candidate_id: int, db: Session, **kwargs) -> Candidate | None:
    """
    Update a candidate by ID.
    Accepts: name, category, photo, active.
    Returns updated candidate or None if not found.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        return None
    
    for key, value in kwargs.items():
        if hasattr(candidate, key) and value is not None:
            setattr(candidate, key, value)
    
    db.commit()
    db.refresh(candidate)
    return candidate


def create_event(name: str, description: str | None, start_time, end_time, db: Session) -> Event:
    """Create a new event."""
    event = Event(
        name=name,
        description=description,
        start_time=start_time,
        end_time=end_time
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def set_event_winner(event_id: int, winner: str, db: Session) -> Event | None:
    """Set the winner for an event. Returns updated event or None if not found."""
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        return None
    
    event.winner = winner
    db.commit()
    db.refresh(event)
    return event


def get_all_votes(db: Session) -> list[dict]:
    """
    Get all votes with voter and candidate details.
    Returns list of dicts: [{ voter_name, voter_roll_number, candidate_name, category, created_at }, ...]
    Sorted by created_at descending (most recent first).
    """
    votes = db.query(
        Student.name.label("voter_name"),
        Student.roll_number.label("voter_roll_number"),
        Candidate.name.label("candidate_name"),
        Vote.category,
        Vote.created_at
    ).join(
        Student, Vote.voter_id == Student.id
    ).join(
        Candidate, Vote.candidate_id == Candidate.id
    ).order_by(desc(Vote.created_at)).all()
    
    return [
        {
            "voter_name": v[0],
            "voter_roll_number": v[1],
            "candidate_name": v[2],
            "category": v[3],
            "created_at": v[4]
        }
        for v in votes
    ]
