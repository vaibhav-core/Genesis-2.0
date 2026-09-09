from datetime import datetime
from typing import Literal
from pydantic import BaseModel
from pydantic import model_validator


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
    event_id: int
    name: str
    gender: str | None = None
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
    event_id: int
    candidate_id: int
    voter_id: int | None = None
    free_voter_identifier: str | None = None


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
    event_id: int | None = None


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
    event_id: int
    name: str
    gender: str | None = None
    photo: str | None = None
    active: bool

    class Config:
        from_attributes = True


# Voting - Verify
class VotingVerifyRequest(BaseModel):
    mode: Literal["registered", "free"]
    event_id: int
    candidate_id: int
    roll_number: str | None = None
    name: str | None = None
    voter_identifier: str | None = None

    @model_validator(mode="after")
    def validate_mode_fields(self):
        if self.mode == "registered" and (not self.roll_number or not self.name):
            raise ValueError("registered mode requires roll_number and name")
        if self.mode == "free" and not self.voter_identifier:
            raise ValueError("free mode requires voter_identifier")
        return self


class VotingVerifyResponseSuccess(BaseModel):
    valid: bool = True
    already_voted: bool = False


class VotingVerifyResponseFailure(BaseModel):
    valid: bool = False
    reason: str  # "identity_mismatch", "student_not_found", "not_eligible"
    message: str | None = None


# Voting - Vote Submission
class VoteRequest(BaseModel):
    mode: Literal["registered", "free"]
    event_id: int
    candidate_id: int
    roll_number: str | None = None
    name: str | None = None
    voter_identifier: str | None = None

    @model_validator(mode="after")
    def validate_mode_fields(self):
        if self.mode == "registered" and (not self.roll_number or not self.name):
            raise ValueError("registered mode requires roll_number and name")
        if self.mode == "free" and not self.voter_identifier:
            raise ValueError("free mode requires voter_identifier")
        return self


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
    event_id: int
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
    event_id: int
    name: str
    gender: str | None = None
    photo: str | None = None


# Admin - Update Candidate
class AdminUpdateCandidateRequest(BaseModel):
    name: str | None = None
    gender: str | None = None
    photo: str | None = None
    active: bool | None = None


# Admin - Create Event
class AdminCreateEventRequest(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    competition_format: Literal["individual", "team"] | None = None
    voting_enabled: bool = False
    is_competitive: bool = False
    pass_distribution_enabled_override: bool = False


class AdminUpdateEventRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    competition_format: Literal["individual", "team"] | None = None
    voting_enabled: bool | None = None
    is_competitive: bool | None = None
    pass_distribution_enabled_override: bool | None = None


# Admin - Set Event Winner
class AdminSetEventWinnerRequest(BaseModel):
    winner: str | None = None
    winner_participant_id: int | None = None

    @model_validator(mode="after")
    def require_winner(self):
        if self.winner is None and self.winner_participant_id is None:
            raise ValueError("winner or winner_participant_id is required")
        return self


class TeamMemberInput(BaseModel):
    name: str
    roll_number: str | None = None


class AdminCreateParticipantRequest(BaseModel):
    participant_type: Literal["individual", "team"]
    name: str
    roll_number: str | None = None
    members: list[TeamMemberInput] | None = None
    gender: Literal["male", "female", "other"] | None = None
    photo: str | None = None

    @model_validator(mode="after")
    def validate_members(self):
        if self.participant_type == "individual" and self.members is not None:
            raise ValueError("individual participants cannot include members")
        if self.participant_type == "team" and not self.members:
            raise ValueError("team participants require at least one member")
        return self


class TeamMemberResponse(BaseModel):
    id: int
    name: str
    roll_number: str | None = None

    class Config:
        from_attributes = True


class ParticipantResponse(BaseModel):
    id: int
    event_id: int
    participant_type: str
    name: str
    roll_number: str | None = None
    members: list[TeamMemberResponse] = []
    gender: str | None = None
    photo: str | None = None


# Admin - Vote Record
class AdminVoteRecord(BaseModel):
    voter_name: str
    voter_roll_number: str | None = None
    candidate_name: str
    event_id: int
    created_at: datetime
    free_voter_identifier: str | None = None


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
    location: str | None = None
    competition_format: str | None = None
    voting_enabled: bool = False
    is_competitive: bool = False
    voting_status: str = "not_started"
    winner: str | None = None
    winner_participant_id: int | None = None
    winner_photo: str | None = None
    pass_distribution_enabled_override: bool = False

    class Config:
        from_attributes = True
