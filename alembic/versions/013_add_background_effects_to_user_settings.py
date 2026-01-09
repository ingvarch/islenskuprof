"""Add background_effects to user_settings

Revision ID: 013
Revises: 012
Create Date: 2026-01-06

"""

from alembic import op
import sqlalchemy as sa
import logging

# Get logger
logger = logging.getLogger("alembic.runtime.migration")

# revision identifiers, used by Alembic.
revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade():
    logger.info(
        "Applying migration %s: Adding background_effects to user_settings", revision
    )

    # Add background_effects column to user_settings table with default False
    op.add_column(
        "user_settings",
        sa.Column("background_effects", sa.Boolean, nullable=False, server_default="0"),
    )

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info(
        "Rolling back migration %s: Removing background_effects from user_settings",
        revision,
    )

    # Remove background_effects column from user_settings table
    op.drop_column("user_settings", "background_effects")

    logger.info("Migration %s rolled back successfully", revision)
