"""Add communication table

Revision ID: 007
Revises: 006
Create Date: 2023-12-22

"""

from alembic import op
import sqlalchemy as sa
import logging

# Get logger
logger = logging.getLogger("alembic.runtime.migration")

# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Applying migration %s: Adding communication table", revision)

    # Create communication table
    op.create_table(
        "communication",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("topic_id", sa.Integer, nullable=False),
        sa.Column("image_url", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=False),
    )

    # Create foreign key constraint
    op.create_foreign_key(
        "fk_communication_topic_id", "communication", "topic", ["topic_id"], ["id"]
    )

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info("Rolling back migration %s: Removing communication table", revision)

    # Remove foreign key constraint
    op.drop_constraint("fk_communication_topic_id", "communication", type_="foreignkey")

    # Drop communication table
    op.drop_table("communication")

    logger.info("Migration %s rolled back successfully", revision)
