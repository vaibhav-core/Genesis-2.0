from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase


DATABASE_URL = "sqlite:///./data/freshers.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_sqlite_schema():
    """Apply small additive schema updates for the file-based SQLite database."""
    with engine.begin() as conn:
        columns = conn.execute(text("PRAGMA table_info(events)")).fetchall()
        if not any(column[1] == "winner_participant_id" for column in columns):
            conn.execute(text(
                "ALTER TABLE events ADD COLUMN winner_participant_id "
                "INTEGER REFERENCES participants(id)"
            ))