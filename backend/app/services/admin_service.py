"""
Admin service: candidates, events, and vote management.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models import Candidate, Event, Participant, TeamMember, Vote, Student
from .student_service import normalize_roll


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


def set_event_winner_participant(
    event_id: int, participant_id: int, db: Session
) -> Event | None:
    """Set an event winner from one of its registered participants."""
    event = db.query(Event).filter(Event.id == event_id).first()
    participant = db.query(Participant).filter(
        Participant.id == participant_id,
        Participant.event_id == event_id,
    ).first()

    if not event or not participant:
        return None

    event.winner_participant_id = participant.id
    event.winner = participant.name
    db.commit()
    db.refresh(event)
    return event


def create_participant(
    event_id: int,
    participant_type: str,
    name: str,
    roll_number: str | None,
    members: list,
    db: Session,
) -> Participant | None:
    """Create an individual or team participant for an existing event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return None

    participant = Participant(
        event_id=event_id,
        participant_type=participant_type,
        name=name,
        roll_number=normalize_roll(roll_number) if roll_number else None,
    )
    if participant_type == "team":
        participant.members = [
            TeamMember(
                name=member.name,
                roll_number=normalize_roll(member.roll_number)
                if member.roll_number else None,
            )
            for member in members
        ]
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def get_event_participants(event_id: int, db: Session) -> list[Participant] | None:
    """Return participants for an event, or None when the event is missing."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return None
    return db.query(Participant).filter(Participant.event_id == event_id).all()


def delete_event_participant(
    event_id: int, participant_id: int, db: Session
) -> bool:
    """Delete a participant belonging to an event and clear any winner reference."""
    participant = db.query(Participant).filter(
        Participant.id == participant_id,
        Participant.event_id == event_id,
    ).first()
    if not participant:
        return False

    event = db.query(Event).filter(Event.id == event_id).first()
    if event and event.winner_participant_id == participant_id:
        event.winner_participant_id = None
    db.delete(participant)
    db.commit()
    return True


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
