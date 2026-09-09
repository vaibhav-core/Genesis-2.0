from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase


DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "freshers.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

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


def ensure_event_columns() -> None:
    """Add any Event columns that exist on the model but are missing in the DB.

    This is a safe, data-preserving repair for SQLite databases that drifted after
    ad-hoc schema edits and are missing a subset of newer Event fields.
    """
    with engine.begin() as conn:
        existing_tables = {
            row[0] for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type = 'table'"))
        }
        if "events" not in existing_tables:
            Base.metadata.create_all(bind=engine)
            return

        existing_columns = {
            row[1] for row in conn.execute(text("PRAGMA table_info(events)"))
        }

        column_defs = [
            ("location", "VARCHAR(150)", None),
            ("competition_format", "VARCHAR(20)", None),
            ("voting_enabled", "BOOLEAN", "0"),
            ("is_competitive", "BOOLEAN", "0"),
            ("voting_status", "VARCHAR(20)", "'not_started'"),
            ("winner", "VARCHAR(100)", None),
            ("winner_participant_id", "INTEGER", None),
            ("winner_photo", "VARCHAR(255)", None),
            ("pass_distribution_enabled_override", "BOOLEAN", "0"),
        ]

        for column_name, column_type, default in column_defs:
            if column_name in existing_columns:
                continue

            if default is None:
                conn.execute(text(f'ALTER TABLE events ADD COLUMN "{column_name}" {column_type}'))
            else:
                conn.execute(text(f'ALTER TABLE events ADD COLUMN "{column_name}" {column_type} DEFAULT {default}'))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()