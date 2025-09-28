"""Add selftracking table

Revision ID: 1026bee50450
Revises:
Create Date: 2025-09-13 10:46:44.365861

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "1026bee50450"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "selftracking",
        sa.Column("id", sa.Integer, primary_key=True, unique=True, autoincrement=True),
        sa.Column("path", sa.String, nullable=False),
        sa.Column("user", sa.String, nullable=True),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("track_time", sa.DateTime, default=sa.TIMESTAMP),
        sa.Column("extras", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("idx_selftracking_path", "selftracking", ["path"])
    op.create_index("idx_selftracking_track_time", "selftracking", ["track_time"])


def downgrade():
    op.drop_index("idx_selftracking_track_time", table_name="selftracking")
    op.drop_index("idx_selftracking_path", table_name="selftracking")

    op.drop_table("selftracking")
