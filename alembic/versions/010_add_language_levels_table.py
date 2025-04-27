"""Add language_levels table and language_level_id to user_settings

Revision ID: 010
Revises: 009
Create Date: 2023-12-25

"""
from alembic import op
import sqlalchemy as sa
import logging

# Get logger
logger = logging.getLogger('alembic.runtime.migration')

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Applying migration %s: Adding language_levels table and language_level_id to user_settings", revision)

    # Create language_levels table
    op.create_table(
        'language_levels',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('level', sa.String, nullable=False, unique=True)
    )

    # Insert language levels
    op.bulk_insert(
        sa.table(
            'language_levels',
            sa.column('level', sa.String)
        ),
        [
            {'level': 'A1'},
            {'level': 'A2'},
            {'level': 'B1'},
            {'level': 'B2'},
            {'level': 'C1'},
            {'level': 'C2'}
        ]
    )

    # Add language_level_id column to user_settings table
    op.add_column('user_settings', sa.Column('language_level_id', sa.Integer, nullable=True))

    # Create foreign key constraint
    op.create_foreign_key(
        'fk_user_settings_language_level_id',
        'user_settings', 'language_levels',
        ['language_level_id'], ['id']
    )

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info("Rolling back migration %s: Removing language_level_id from user_settings and dropping language_levels table", revision)

    # Remove foreign key constraint
    op.drop_constraint('fk_user_settings_language_level_id', 'user_settings', type_='foreignkey')

    # Remove language_level_id column from user_settings table
    op.drop_column('user_settings', 'language_level_id')

    # Drop language_levels table
    op.drop_table('language_levels')

    logger.info("Migration %s rolled back successfully", revision)
