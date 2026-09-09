"""Add event competition metadata."""
from alembic import op
import sqlalchemy as sa

revision = "0001_event_competition_fields"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("events", sa.Column("is_competitive", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table("events", recreate="always") as batch:
        batch.drop_column("voting_status")
        batch.drop_column("is_competitive")
        batch.drop_column("voting_enabled")
        batch.drop_column("competition_format")
        batch.drop_column("location")