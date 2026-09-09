"""Migration tests against a copy of the checked-in legacy database shape."""

import os
import shutil
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


ROOT = Path(__file__).resolve().parents[1]
LEGACY_DB = ROOT / "data" / "freshers.db"


def run_migration(command_name: str, database_url: str):
    config = Config(str(ROOT / "alembic.ini"))
    os.environ["DATABASE_URL"] = database_url
    getattr(command, command_name)(config, "head" if command_name == "upgrade" else "base")


def test_legacy_database_upgrades_and_rolls_back(tmp_path):
    copy_path = tmp_path / "freshers-migration.db"
    shutil.copy2(LEGACY_DB, copy_path)
    database_url = f"sqlite:///{copy_path.as_posix()}"

    try:
        run_migration("upgrade", database_url)
        inspector = inspect(create_engine(database_url))
        event_columns = {column["name"] for column in inspector.get_columns("events")}
        candidate_columns = {column["name"] for column in inspector.get_columns("candidates")}
        vote_columns = {column["name"] for column in inspector.get_columns("votes")}
        participant_columns = {column["name"] for column in inspector.get_columns("participants")}

        assert {"location", "is_competitive", "voting_status", "pass_distribution_enabled_override", "winner_photo"} <= event_columns
        assert {"event_id", "gender"} <= candidate_columns
        assert {"event_id", "free_voter_identifier"} <= vote_columns
        assert {"gender", "photo"} <= participant_columns

        run_migration("downgrade", database_url)
        inspector = inspect(create_engine(database_url))
        assert "location" not in {column["name"] for column in inspector.get_columns("events")}
        assert "event_id" not in {column["name"] for column in inspector.get_columns("candidates")}
    finally:
        os.environ.pop("DATABASE_URL", None)
