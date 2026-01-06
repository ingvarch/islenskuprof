"""Change background_effects from Boolean to String for preset selection

Revision ID: 014
Revises: 013
Create Date: 2026-01-06

"""
from alembic import op
import sqlalchemy as sa
import logging

# Get logger
logger = logging.getLogger('alembic.runtime.migration')

# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Applying migration %s: Changing background_effects from Boolean to String", revision)

    # SQLite doesn't support ALTER COLUMN, so we need to:
    # 1. Create a new column
    # 2. Copy data (convert True -> "auto", False -> "off")
    # 3. Drop old column
    # 4. Rename new column

    # Add new string column
    op.add_column('user_settings', sa.Column('background_effects_new', sa.String, nullable=False, server_default='off'))

    # Copy data: True -> "auto", False -> "off"
    op.execute("UPDATE user_settings SET background_effects_new = CASE WHEN background_effects = 1 THEN 'auto' ELSE 'off' END")

    # Drop old column
    op.drop_column('user_settings', 'background_effects')

    # Rename new column to original name
    op.alter_column('user_settings', 'background_effects_new', new_column_name='background_effects')

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info("Rolling back migration %s: Changing background_effects from String back to Boolean", revision)

    # Add boolean column back
    op.add_column('user_settings', sa.Column('background_effects_old', sa.Boolean, nullable=False, server_default='0'))

    # Copy data: "off" -> False, anything else -> True
    op.execute("UPDATE user_settings SET background_effects_old = CASE WHEN background_effects = 'off' THEN 0 ELSE 1 END")

    # Drop string column
    op.drop_column('user_settings', 'background_effects')

    # Rename column back
    op.alter_column('user_settings', 'background_effects_old', new_column_name='background_effects')

    logger.info("Migration %s rolled back successfully", revision)
