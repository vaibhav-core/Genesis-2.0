from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event
from ..schemas import EventResponse


router = APIRouter(prefix="/api/events", tags=["Events"])


@router.get("")
def get_all_events(db: Session = Depends(get_db)):
    """
    Get all events (public endpoint).
    """
    events = db.query(Event).all()
    return [EventResponse(**e.__dict__) for e in events]


@router.get("/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)):
    """
    Get a single event by ID (public endpoint).
    Returns 404 if not found.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return EventResponse(**event.__dict__)
