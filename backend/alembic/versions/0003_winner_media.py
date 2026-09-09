"""Add an optional event winner photo."""
from alembic import op
import sqlalchemy as sa

revision = "0003_winner_media"
down_revision = "0002_pass_distribution_override"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("events", sa.Column("winner_photo", sa.String(255), nullable=True))


def downgrade():
    with op.batch_alter_table("events", recreate="always") as batch:
        batch.drop_column("winner_photo")