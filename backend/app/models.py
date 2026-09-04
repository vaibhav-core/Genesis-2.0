from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    roll_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    branch: Mapped[str | None] = mapped_column(String(50))
    year: Mapped[int | None]
    eligible_to_vote: Mapped[bool] = mapped_column(Boolean, default=True)