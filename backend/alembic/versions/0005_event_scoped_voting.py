"""Move candidates and votes from free-text categories to events."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "0005_event_scoped_voting"
down_revision = "0004_participant_media"
branch_labels = None
depends_on = None


def _columns(bind, table):
    return {column["name"] for column in inspect(bind).get_columns(table)}


def _drop_index_if_present(bind, table, name):
    if any(index["name"] == name for index in inspect(bind).get_indexes(table)):
        op.drop_index(name, table_name=table)


def upgrade():
    bind = op.get_bind()
    candidate_columns = _columns(bind, "candidates")
    vote_columns = _columns(bind, "votes")

    if "event_id" not in candidate_columns:
        op.add_column("candidates", sa.Column("event_id", sa.Integer(), nullable=True))
    if "gender" not in candidate_columns:
        op.add_column("candidates", sa.Column("gender", sa.String(20), nullable=True))

    if "category" in candidate_columns:
        categories = bind.execute(text("SELECT DISTINCT category FROM candidates WHERE category IS NOT NULL")).scalars().all()
        for category in categories:
            event_id = bind.execute(
                text("SELECT id FROM events WHERE lower(name) = lower(:name) LIMIT 1"),
                {"name": category},
            ).scalar()
            if event_id is None:
                event_id = bind.execute(
                    text("INSERT INTO events (name, is_competitive, voting_enabled, voting_status) VALUES (:name, 1, 0, 'not_started') RETURNING id"),
                    {"name": category},
                ).scalar()
            bind.execute(text("UPDATE candidates SET event_id = :event_id WHERE category = :category"), {"event_id": event_id, "category": category})

        _drop_index_if_present(bind, "candidates", "ix_candidates_category")
        with op.batch_alter_table("candidates", recreate="always") as batch:
            batch.drop_column("category")
            batch.alter_column("event_id", existing_type=sa.Integer(), nullable=False)
            batch.create_foreign_key("fk_candidates_event_id", "events", ["event_id"], ["id"])
            batch.create_index("ix_candidates_event_id", ["event_id"])

    if "event_id" not in vote_columns:
        op.add_column("votes", sa.Column("event_id", sa.Integer(), nullable=True))
    if "free_voter_identifier" not in vote_columns:
        op.add_column("votes", sa.Column("free_voter_identifier", sa.String(100), nullable=True))

    if "category" in vote_columns:
        bind.execute(text("UPDATE votes SET event_id = (SELECT event_id FROM candidates WHERE candidates.id = votes.candidate_id)"))
        _drop_index_if_present(bind, "votes", "ix_votes_category")
        with op.batch_alter_table("votes", recreate="always") as batch:
            batch.drop_constraint("uq_one_vote_per_category", type_="unique")
            batch.drop_column("category")
            batch.alter_column("event_id", existing_type=sa.Integer(), nullable=False)
            batch.alter_column("voter_id", existing_type=sa.Integer(), nullable=True)
            batch.create_foreign_key("fk_votes_event_id", "events", ["event_id"], ["id"])
            batch.create_unique_constraint("uq_one_vote_per_event_registered", ["voter_id", "event_id"])
            batch.create_unique_constraint("uq_one_vote_per_event_free", ["free_voter_identifier", "event_id"])
            batch.create_index("ix_votes_event_id", ["event_id"])


def downgrade():
    bind = op.get_bind()
    if bind.execute(text("SELECT COUNT(*) FROM votes WHERE voter_id IS NULL")).scalar():
        raise RuntimeError("Cannot downgrade event-scoped voting while free-mode votes exist")

    _drop_index_if_present(bind, "votes", "ix_votes_event_id")
    with op.batch_alter_table("votes", recreate="always") as batch:
        batch.drop_constraint("uq_one_vote_per_event_registered", type_="unique")
        batch.drop_constraint("uq_one_vote_per_event_free", type_="unique")
        batch.drop_column("free_voter_identifier")
        batch.add_column(sa.Column("category", sa.String(50), nullable=True))
        batch.alter_column("voter_id", existing_type=sa.Integer(), nullable=False)
        batch.create_unique_constraint("uq_one_vote_per_category", ["voter_id", "category"])

    bind.execute(text("UPDATE votes SET category = (SELECT name FROM events WHERE events.id = votes.event_id)"))
    with op.batch_alter_table("votes", recreate="always") as batch:
        batch.drop_column("event_id")
        batch.alter_column("category", existing_type=sa.String(50), nullable=False)

    _drop_index_if_present(bind, "candidates", "ix_candidates_event_id")
    with op.batch_alter_table("candidates", recreate="always") as batch:
        batch.add_column(sa.Column("category", sa.String(50), nullable=True))
    bind.execute(text("UPDATE candidates SET category = (SELECT name FROM events WHERE events.id = candidates.event_id)"))
    with op.batch_alter_table("candidates", recreate="always") as batch:
        batch.drop_column("event_id")
        batch.drop_column("gender")
        batch.alter_column("category", existing_type=sa.String(50), nullable=False)