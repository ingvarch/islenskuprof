"""Add audio_speeds and user_settings tables

Revision ID: 008
Revises: 007
Create Date: 2023-12-23

"""
from alembic import op
import sqlalchemy as sa
import logging

# Get logger
logger = logging.getLogger('alembic.runtime.migration')

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Applying migration %s: Adding audio_speeds and user_settings tables", revision)

    # Create audio_speeds table
    op.create_table(
        'audio_speeds',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('speed', sa.Float, nullable=False),
        sa.Column('description', sa.String, nullable=True)
    )

    # Insert default audio speed values
    op.bulk_insert(
        sa.table(
            'audio_speeds',
            sa.column('speed', sa.Float),
            sa.column('description', sa.String)
        ),
        [
            {'speed': 0.5, 'description': 'Very Slow'},
            {'speed': 0.75, 'description': 'Slow'},
            {'speed': 1.0, 'description': 'Normal'},
            {'speed': 1.5, 'description': 'Fast'}
        ]
    )

    # Create user_settings table
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('audio_speed_id', sa.Integer, nullable=False)
    )

    # Create foreign key constraints
    op.create_foreign_key(
        'fk_user_settings_user_id',
        'user_settings', 'users',
        ['user_id'], ['id']
    )

    op.create_foreign_key(
        'fk_user_settings_audio_speed_id',
        'user_settings', 'audio_speeds',
        ['audio_speed_id'], ['id']
    )

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info("Rolling back migration %s: Removing user_settings and audio_speeds tables", revision)

    # Remove foreign key constraints
    op.drop_constraint('fk_user_settings_audio_speed_id', 'user_settings', type_='foreignkey')
    op.drop_constraint('fk_user_settings_user_id', 'user_settings', type_='foreignkey')

    # Drop tables
    op.drop_table('user_settings')
    op.drop_table('audio_speeds')

    logger.info("Migration %s rolled back successfully", revision)
