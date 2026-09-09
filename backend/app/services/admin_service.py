"""
Admin service: candidates, events, and vote management.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models import Candidate, Event, Participant, TeamMember, Vote, Student
from .student_service import normalize_roll


def create_candidate(event_id: int, name: str, gender: str | None, photo: str | None, db: Session) -> Candidate | None:
    """Create a candidate for a voting-enabled event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or not event.is_competitive or not event.voting_enabled:
        return None
    candidate = Candidate(
        event_id=event_id,
        name=name,
        gender=gender,
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


def create_event(name: str, description: str | None, location: str | None, start_time, end_time, competition_format: str | None, voting_enabled: bool, is_competitive: bool, pass_distribution_enabled_override: bool, db: Session) -> Event:
    """Create a new event."""
    event = Event(
        name=name,
        description=description,
        location=location,
        start_time=start_time,
        end_time=end_time,
        competition_format=competition_format,
        voting_enabled=voting_enabled,
        is_competitive=is_competitive or voting_enabled or competition_format is not None,
        pass_distribution_enabled_override=pass_distribution_enabled_override,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def set_event_winner(
    event_id: int,
    winner: str | None,
    winner_participant_id: int | None,
    db: Session,
) -> Event | None:
    """Set an event winner by text or by a participant belonging to the event."""
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        return None

    if winner_participant_id is not None:
        participant = db.query(Participant).filter(
            Participant.id == winner_participant_id,
            Participant.event_id == event_id,
        ).first()
        if not participant:
            return None
        event.winner = participant.name
        event.winner_participant_id = participant.id
        event.winner_photo = participant.photo
    else:
        event.winner = winner
        event.winner_participant_id = None
        event.winner_photo = None

    db.commit()
    db.refresh(event)
    return event


def update_event(event_id: int, db: Session, **kwargs) -> Event | None:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return None
    for key, value in kwargs.items():
        setattr(event, key, value)
    db.commit()
    db.refresh(event)
    return event


def set_voting_status(event_id: int, status: str, db: Session) -> Event | None:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or (status == "open" and not event.voting_enabled):
        return None
    event.voting_status = status
    db.commit()
    db.refresh(event)
    return event


def delete_event(event_id: int, db: Session) -> bool:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return False
    db.query(Vote).filter(Vote.event_id == event_id).delete(synchronize_session=False)
    candidate_ids = [row[0] for row in db.query(Candidate.id).filter(Candidate.event_id == event_id).all()]
    if candidate_ids:
        db.query(Vote).filter(Vote.candidate_id.in_(candidate_ids)).delete(synchronize_session=False)
        db.query(Candidate).filter(Candidate.id.in_(candidate_ids)).delete(synchronize_session=False)
    participant_ids = [row[0] for row in db.query(Participant.id).filter(Participant.event_id == event_id).all()]
    if participant_ids:
        event.winner_participant_id = None
        db.flush()
        db.query(TeamMember).filter(TeamMember.participant_id.in_(participant_ids)).delete(synchronize_session=False)
        db.query(Participant).filter(Participant.id.in_(participant_ids)).delete(synchronize_session=False)
    db.delete(event)
    db.commit()
    return True


def create_participant(
    event_id: int,
    participant_type: str,
    name: str,
    roll_number: str | None,
    members: list[dict] | None,
    gender: str | None,
    photo: str | None,
    db: Session,
) -> Participant | None:
    """Create an individual or team participant for an existing event."""
    if participant_type not in {"individual", "team"}:
        raise ValueError("participant_type must be 'individual' or 'team'")

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return None

    if event.competition_format and event.competition_format != participant_type:
        raise ValueError("Participant type does not match event competition format")

    participant = Participant(
        event_id=event_id,
        participant_type=participant_type,
        name=name,
        roll_number=normalize_roll(roll_number) if roll_number is not None else None,
        gender=gender,
        photo=photo,
    )
    if members:
        participant.team_members = [
            TeamMember(
                name=member["name"],
                roll_number=(
                    normalize_roll(member["roll_number"])
                    if member.get("roll_number") is not None else None
                ),
            )
            for member in members
        ]

    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def event_is_competitive(event: Event) -> bool:
    return bool(event and (event.is_competitive or event.voting_enabled or event.competition_format))


def pass_distribution_available(event: Event, now=None) -> bool:
    from datetime import datetime
    now = now or datetime.utcnow()
    return bool(event and (event.pass_distribution_enabled_override or not event.start_time or now >= event.start_time))


def get_event_participants(event_id: int, db: Session) -> list[Participant] | None:
    """Return participants for an event, or None when the event does not exist."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return None
    return db.query(Participant).filter(Participant.event_id == event_id).all()


def delete_participant(event_id: int, participant_id: int, db: Session) -> bool:
    """Delete a participant only when it belongs to the requested event."""
    participant = db.query(Participant).filter(
        Participant.id == participant_id,
        Participant.event_id == event_id,
    ).first()
    if not participant:
        return False
    db.delete(participant)
    db.commit()
    return True


def get_all_votes(db: Session) -> list[dict]:
    """
    Get all votes with voter and candidate details.
    Free-mode votes are included even though they have no linked Student.
    Sorted by created_at descending (most recent first).
    """
    votes = db.query(
        Student.name.label("voter_name"),
        Student.roll_number.label("voter_roll_number"),
        Candidate.name.label("candidate_name"),
        Vote.event_id,
        Vote.created_at,
        Vote.free_voter_identifier,
    ).outerjoin(
        Student, Vote.voter_id == Student.id
    ).join(
        Candidate, Vote.candidate_id == Candidate.id
    ).order_by(desc(Vote.created_at)).all()
    
    return [
        {
            "voter_roll_number": v[1],
            "candidate_name": v[2],
            "event_id": v[3],
            "created_at": v[4],
            "free_voter_identifier": v[5],
            "voter_name": v[0] or "Free vote",
        }
        for v in votes
    ]
