from fastapi import APIRouter, Depends, HTTPException, status, Header, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AdminUser
from ..security import authenticate_admin, create_admin_token, verify_admin_token, ADMIN_JWT_EXPIRY_HOURS
from ..schemas import (
    AdminLoginRequest, 
    AdminLoginResponse,
    AdminCreateCandidateRequest,
    AdminUpdateCandidateRequest,
    AdminCreateEventRequest,
    AdminUpdateEventRequest,
    AdminSetEventWinnerRequest,
    AdminCreateParticipantRequest,
    AdminVoteRecord,
    CandidateResponse,
    EventResponse,
    ParticipantResponse,
)
from ..services.admin_service import (
    create_candidate,
    update_candidate,
    create_event,
    delete_event,
    update_event,
    set_voting_status,
    set_event_winner,
    get_all_votes,
    create_participant,
    get_event_participants,
    delete_participant,
)


router = APIRouter(prefix="/api/admin", tags=["Admin"])


def get_current_admin_token(authorization: str | None = Header(None)) -> str:
    """
    Dependency to extract and validate JWT token from Authorization header.
    Raises 401 if missing or invalid.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format"
        )
    
    token = parts[1]
    # Verify token (raises 401 if invalid)
    payload = verify_admin_token(token)
    return token


def get_current_admin(
    token: str = Depends(get_current_admin_token),
    db: Session = Depends(get_db)
) -> AdminUser:
    """
    Dependency to get current authenticated admin.
    Used on all protected endpoints.
    """
    payload = verify_admin_token(token)
    admin_id = payload.get("admin_id")
    
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin user not found"
        )
    
    return admin


@router.post("/login")
def admin_login(
    request: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Admin login endpoint.
    Returns JWT token on successful authentication.
    """
    admin = authenticate_admin(request.username, request.password, db)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create JWT token
    access_token = create_admin_token(admin.id, admin.username)
    
    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ADMIN_JWT_EXPIRY_HOURS * 3600  # Convert hours to seconds
    )


@router.get("/votes")
def get_votes(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all votes (admin only).
    Returns list of vote records with voter and candidate details.
    """
    votes = get_all_votes(db)
    return [AdminVoteRecord(**v) for v in votes]


@router.post("/candidates")
def create_new_candidate(
    request: AdminCreateCandidateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new candidate (admin only).
    """
    candidate = create_candidate(
        request.event_id,
        request.name,
        request.gender,
        request.photo,
        db
    )
    if not candidate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event not found or voting is not enabled")
    return CandidateResponse(**candidate.__dict__)


@router.patch("/candidates/{candidate_id}")
def update_candidate_endpoint(
    candidate_id: int,
    request: AdminUpdateCandidateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update a candidate (admin only).
    """
    # Build kwargs from request, excluding None values
    kwargs = {k: v for k, v in request.model_dump().items() if v is not None}
    
    candidate = update_candidate(candidate_id, db, **kwargs)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    return CandidateResponse(**candidate.__dict__)


@router.post("/events")
def create_new_event(
    request: AdminCreateEventRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new event (admin only).
    """
    event = create_event(
        request.name,
        request.description,
        request.location,
        request.start_time,
        request.end_time,
        request.competition_format,
        request.voting_enabled,
        db
    )
    return EventResponse(**event.__dict__)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_endpoint(
    event_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if not delete_event(event_id, db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/events/{event_id}")
def update_event_endpoint(
    event_id: int,
    request: AdminUpdateEventRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    event = update_event(event_id, db, **request.model_dump(exclude_unset=True))
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return EventResponse(**event.__dict__)


@router.post("/events/{event_id}/voting/start")
def start_voting(event_id: int, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    event = set_voting_status(event_id, "open", db)
    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event not found or voting is not enabled")
    return EventResponse(**event.__dict__)


@router.post("/events/{event_id}/voting/stop")
def stop_voting(event_id: int, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    event = set_voting_status(event_id, "closed", db)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return EventResponse(**event.__dict__)


@router.post("/events/{event_id}/winner")
def set_winner(
    event_id: int,
    request: AdminSetEventWinnerRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Set the winner for an event (admin only).
    """
    event = set_event_winner(
        event_id,
        request.winner,
        request.winner_participant_id,
        db,
    )
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return EventResponse(**event.__dict__)


def participant_response(participant) -> ParticipantResponse:
    return ParticipantResponse(
        id=participant.id,
        event_id=participant.event_id,
        participant_type=participant.participant_type,
        name=participant.name,
        roll_number=participant.roll_number,
        members=participant.team_members,
    )


@router.post("/events/{event_id}/participants", status_code=status.HTTP_201_CREATED)
def add_participant(
    event_id: int,
    request: AdminCreateParticipantRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        participant = create_participant(
            event_id,
            request.participant_type,
            request.name,
            request.roll_number,
            [member.model_dump() for member in request.members] if request.members else None,
            db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return participant_response(participant)


@router.get("/events/{event_id}/participants", response_model=list[ParticipantResponse])
def list_participants(
    event_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    participants = get_event_participants(event_id, db)
    if participants is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return [participant_response(participant) for participant in participants]


@router.delete("/events/{event_id}/participants/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_participant(
    event_id: int,
    participant_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if not delete_participant(event_id, participant_id, db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
