"""Update users table

Revision ID: 004
Revises: 003
Create Date: 2023-12-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import logging

# Get logger
logger = logging.getLogger('alembic.runtime.migration')

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Applying migration %s: Updating users table - changing telegram_id to BigInteger and adding is_premium field", revision)

    # Change telegram_id from Integer to BigInteger
    op.alter_column('users', 'telegram_id',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False,
                    existing_unique=True,
                    existing_index=True)

    # Add is_premium column
    op.add_column('users', sa.Column('is_premium', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info("Rolling back migration %s: Reverting users table changes", revision)

    # Remove is_premium column
    op.drop_column('users', 'is_premium')

    # Change telegram_id back to Integer
    op.alter_column('users', 'telegram_id',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    existing_unique=True,
                    existing_index=True)

    logger.info("Migration %s rolled back successfully", revision)
