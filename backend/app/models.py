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
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    photo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(primary_key=True)
    voter_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("voter_id", "category", name="uq_one_vote_per_category"),
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
    winner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    winner_participant_id: Mapped[int | None] = mapped_column(
        ForeignKey("participants.id"), nullable=True
    )

    participants: Mapped[list["Participant"]] = relationship(
        "Participant",
        back_populates="event",
        foreign_keys="Participant.event_id",
        cascade="all, delete-orphan",
    )
    winner_participant: Mapped["Participant | None"] = relationship(
        "Participant",
        foreign_keys=[winner_participant_id],
    )


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"), nullable=False, index=True
    )
    participant_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    roll_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    event: Mapped[Event] = relationship(
        "Event", back_populates="participants", foreign_keys=[event_id]
    )
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember", back_populates="participant", cascade="all, delete-orphan"
    )


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    roll_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    participant: Mapped[Participant] = relationship(
        "Participant", back_populates="members"
    )