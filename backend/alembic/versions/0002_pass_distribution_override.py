"""Add the manual pass distribution override."""
from alembic import op
import sqlalchemy as sa

revision = "0002_pass_distribution_override"
down_revision = "0001_event_competition_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("events", sa.Column("pass_distribution_enabled_override", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table("events", recreate="always") as batch:
        batch.drop_column("pass_distribution_enabled_override")