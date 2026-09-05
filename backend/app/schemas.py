from datetime import datetime
from pydantic import BaseModel


# Student Schemas
class StudentBase(BaseModel):
    roll_number: str
    name: str
    branch: str | None = None
    year: int | None = None
    eligible_to_vote: bool = True


class StudentCreate(StudentBase):
    pass


class Student(StudentBase):
    id: int

    class Config:
        from_attributes = True


# Candidate Schemas
class CandidateBase(BaseModel):
    name: str
    category: str
    photo: str | None = None
    active: bool = True


class CandidateCreate(CandidateBase):
    pass


class Candidate(CandidateBase):
    id: int

    class Config:
        from_attributes = True


# Vote Schemas
class VoteBase(BaseModel):
    voter_id: int
    candidate_id: int
    category: str


class VoteCreate(VoteBase):
    pass


class Vote(VoteBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# AdminUser Schemas
class AdminUserBase(BaseModel):
    username: str


class AdminUserCreate(AdminUserBase):
    password: str


class AdminUser(AdminUserBase):
    id: int

    class Config:
        from_attributes = True


# Event Schemas
class EventBase(BaseModel):
    name: str
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    winner: str | None = None


class EventCreate(EventBase):
    pass


class Event(EventBase):
    id: int

    class Config:
        from_attributes = True


# ============================================================================
# API Request/Response Schemas (Pass & Voting)
# ============================================================================

# Pass / Student Lookup
class PassVerifyRequest(BaseModel):
    identifier_type: str  # "roll_number" or "name"
    value: str


class PassVerifyResponseStudent(BaseModel):
    roll_number: str
    name: str


class PassVerifyResponseSuccess(BaseModel):
    valid: bool = True
    student: PassVerifyResponseStudent


class PassVerifyResponseFailure(BaseModel):
    valid: bool = False
    reason: str  # "multiple_students_found" or "student_not_found"
    message: str


# Voting - Candidate List
class CandidateResponse(BaseModel):
    id: int
    name: str
    category: str
    photo: str | None = None
    active: bool

    class Config:
        from_attributes = True


# Voting - Verify
class VotingVerifyRequest(BaseModel):
    roll_number: str
    name: str
    category: str


class VotingVerifyResponseSuccess(BaseModel):
    valid: bool = True
    already_voted: bool = False


class VotingVerifyResponseFailure(BaseModel):
    valid: bool = False
    reason: str  # "identity_mismatch", "student_not_found", "not_eligible"
    message: str | None = None


# Voting - Vote Submission
class VoteRequest(BaseModel):
    roll_number: str
    name: str
    candidate_id: int
    category: str


class VoteResponseSuccess(BaseModel):
    success: bool = True


class VoteResponseFailure(BaseModel):
    success: bool = False
    reason: str  # "already_voted", "student_not_found", "identity_mismatch", "not_eligible", "invalid_candidate"
    message: str


# Voting - Results
class VotingResultCandidate(BaseModel):
    candidate_id: int
    name: str
    votes: int


class VotingResultsResponse(BaseModel):
    category: str
    results: list[VotingResultCandidate]


# Admin Login
class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ============================================================================
# Admin Endpoints
# ============================================================================

# Admin - Create Candidate
class AdminCreateCandidateRequest(BaseModel):
    name: str
    category: str
    photo: str | None = None


# Admin - Update Candidate
class AdminUpdateCandidateRequest(BaseModel):
    name: str | None = None
    category: str | None = None
    photo: str | None = None
    active: bool | None = None


# Admin - Create Event
class AdminCreateEventRequest(BaseModel):
    name: str
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


# Admin - Set Event Winner
class AdminSetEventWinnerRequest(BaseModel):
    winner: str


# Admin - Vote Record
class AdminVoteRecord(BaseModel):
    voter_name: str
    voter_roll_number: str
    candidate_name: str
    category: str
    created_at: datetime


# ============================================================================
# Events Endpoints (Public)
# ============================================================================

# Event - Response
class EventResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    winner: str | None = None

    class Config:
        from_attributes = True
