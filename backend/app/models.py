from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    roll_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    branch: Mapped[str | None] = mapped_column(String(50))
    year: Mapped[int | None]
    eligible_to_vote: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    photo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    voter_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), nullable=True)
    free_voter_identifier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("voter_id", "event_id", name="uq_one_vote_per_event_registered"),
        UniqueConstraint("free_voter_identifier", "event_id", name="uq_one_vote_per_event_free"),
    )


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    competition_format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    voting_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    voting_status: Mapped[str] = mapped_column(String(20), default="not_started", nullable=False)
    winner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    winner_participant_id: Mapped[int | None] = mapped_column(
        ForeignKey("participants.id"), nullable=True
    )


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    participant_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    roll_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    team_members: Mapped[list["TeamMember"]] = relationship(
        back_populates="participant",
        cascade="all, delete-orphan",
    )


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    roll_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    participant: Mapped[Participant] = relationship(back_populates="team_members")