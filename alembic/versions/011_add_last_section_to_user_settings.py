"""Add last_section to user_settings

Revision ID: 011
Revises: 010
Create Date: 2023-12-26

"""
from alembic import op
import sqlalchemy as sa
import logging

# Get logger
logger = logging.getLogger('alembic.runtime.migration')

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Applying migration %s: Adding last_section to user_settings", revision)

    # Add last_section column to user_settings table
    op.add_column('user_settings', sa.Column('last_section', sa.String, nullable=True))

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info("Rolling back migration %s: Removing last_section from user_settings", revision)

    # Remove last_section column from user_settings table
    op.drop_column('user_settings', 'last_section')

    logger.info("Migration %s rolled back successfully", revision)
