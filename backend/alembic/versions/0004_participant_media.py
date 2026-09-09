"""Add optional participant gender and photo fields."""
from alembic import op
import sqlalchemy as sa

revision = "0004_participant_media"
down_revision = "0003_winner_media"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("participants", sa.Column("gender", sa.String(20), nullable=True))
    op.add_column("participants", sa.Column("photo", sa.String(255), nullable=True))


def downgrade():
    with op.batch_alter_table("participants", recreate="always") as batch:
        batch.drop_column("photo")
        batch.drop_column("gender")