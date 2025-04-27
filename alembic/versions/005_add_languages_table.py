"""Add languages table and add language_id to users table

Revision ID: 005
Revises: 004
Create Date: 2023-12-20

"""
from alembic import op
import sqlalchemy as sa
import logging

# Get logger
logger = logging.getLogger('alembic.runtime.migration')

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Applying migration %s: Adding languages table and language_id to users table", revision)

    # Create languages table
    op.create_table(
        'languages',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('code', sa.String, nullable=False, unique=True, index=True),
        sa.Column('language', sa.String, nullable=False)
    )

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info("Rolling back migration %s: Removing language_id from users table and dropping languages table", revision)

    # Drop languages table
    op.drop_table('languages')

    logger.info("Migration %s rolled back successfully", revision)
