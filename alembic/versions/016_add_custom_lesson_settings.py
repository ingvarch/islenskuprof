"""Add settings columns to pimsleur_custom_lessons for wizard UX

Revision ID: 016
Revises: 015
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa
import logging

# Get logger
logger = logging.getLogger('alembic.runtime.migration')

# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Applying migration %s: Adding custom lesson settings columns", revision)

    # Add new columns to pimsleur_custom_lessons table
    op.add_column('pimsleur_custom_lessons',
        sa.Column('focus', sa.String(20), nullable=False, server_default='vocabulary'))
    op.add_column('pimsleur_custom_lessons',
        sa.Column('voice_preference', sa.String(10), nullable=False, server_default='both'))
    op.add_column('pimsleur_custom_lessons',
        sa.Column('difficulty_level', sa.String(5), nullable=False, server_default='auto'))
    op.add_column('pimsleur_custom_lessons',
        sa.Column('text_analysis_json', sa.Text, nullable=True))
    op.add_column('pimsleur_custom_lessons',
        sa.Column('error_message', sa.String(500), nullable=True))
    op.add_column('pimsleur_custom_lessons',
        sa.Column('generation_started_at', sa.DateTime, nullable=True))
    op.add_column('pimsleur_custom_lessons',
        sa.Column('generation_completed_at', sa.DateTime, nullable=True))

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info("Rolling back migration %s: Removing custom lesson settings columns", revision)

    op.drop_column('pimsleur_custom_lessons', 'generation_completed_at')
    op.drop_column('pimsleur_custom_lessons', 'generation_started_at')
    op.drop_column('pimsleur_custom_lessons', 'error_message')
    op.drop_column('pimsleur_custom_lessons', 'text_analysis_json')
    op.drop_column('pimsleur_custom_lessons', 'difficulty_level')
    op.drop_column('pimsleur_custom_lessons', 'voice_preference')
    op.drop_column('pimsleur_custom_lessons', 'focus')

    logger.info("Migration %s rolled back successfully", revision)
