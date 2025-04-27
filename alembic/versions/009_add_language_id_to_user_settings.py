"""Add language_id to user_settings table

Revision ID: 009
Revises: 008
Create Date: 2023-12-24

"""
from alembic import op
import sqlalchemy as sa
import logging

# Get logger
logger = logging.getLogger('alembic.runtime.migration')

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Applying migration %s: Adding language_id to user_settings table", revision)

    # Add language_id column to user_settings table
    op.add_column('user_settings', sa.Column('language_id', sa.Integer, nullable=True))

    # Create foreign key constraint
    op.create_foreign_key(
        'fk_user_settings_language_id',
        'user_settings', 'languages',
        ['language_id'], ['id']
    )

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info("Rolling back migration %s: Removing language_id from user_settings table", revision)

    # Remove foreign key constraint
    op.drop_constraint('fk_user_settings_language_id', 'user_settings', type_='foreignkey')

    # Remove language_id column from user_settings table
    op.drop_column('user_settings', 'language_id')

    logger.info("Migration %s rolled back successfully", revision)
