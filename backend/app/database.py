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