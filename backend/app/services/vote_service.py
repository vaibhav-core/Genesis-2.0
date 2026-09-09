from sqlalchemy.orm import Session

from ..models import Event, Vote


def reset_all_votes(db: Session) -> int:
    """Delete every vote record and return the number removed."""
    deleted = db.query(Vote).delete(synchronize_session=False)
    db.query(Event).update({Event.winner: None, Event.winner_participant_id: None}, synchronize_session=False)
    db.commit()
    return deleted