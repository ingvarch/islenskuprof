"""Add multi-language support for target languages

Revision ID: 012
Revises: 011
Create Date: 2025-01-06

This migration adds:
1. target_languages table - available languages for learning
2. language_code column to seed data tables (names, cities, jobs, activities, topics)
3. target_language_id column to user_settings
"""
from alembic import op
import sqlalchemy as sa
import logging

# Get logger
logger = logging.getLogger('alembic.runtime.migration')

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Applying migration %s: Adding multi-language support", revision)

    # 1. Create target_languages table
    op.create_table(
        'target_languages',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(10), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('native_name', sa.String(50), nullable=False)
    )

    # 2. Add language_code column to seed data tables
    # Names table
    op.add_column('names', sa.Column('language_code', sa.String(10), nullable=True))
    op.create_index('ix_names_language_code', 'names', ['language_code'])

    # Cities table
    op.add_column('cities', sa.Column('language_code', sa.String(10), nullable=True))
    op.create_index('ix_cities_language_code', 'cities', ['language_code'])

    # Jobs table
    op.add_column('jobs', sa.Column('language_code', sa.String(10), nullable=True))
    op.create_index('ix_jobs_language_code', 'jobs', ['language_code'])

    # Activities table
    op.add_column('activities', sa.Column('language_code', sa.String(10), nullable=True))
    op.create_index('ix_activities_language_code', 'activities', ['language_code'])

    # Topics table
    op.add_column('topic', sa.Column('language_code', sa.String(10), nullable=True))
    op.create_index('ix_topic_language_code', 'topic', ['language_code'])

    # Persons table (generated from seed data)
    op.add_column('persons', sa.Column('language_code', sa.String(10), nullable=True))
    op.create_index('ix_persons_language_code', 'persons', ['language_code'])

    # 3. Add target_language_id to user_settings
    op.add_column('user_settings', sa.Column('target_language_id', sa.Integer, nullable=True))
    op.create_foreign_key(
        'fk_user_settings_target_language_id',
        'user_settings', 'target_languages',
        ['target_language_id'], ['id']
    )

    # 4. Update existing data to have language_code='is' (all existing data was Icelandic)
    logger.info("Updating existing data with language_code='is'")
    op.execute("UPDATE names SET language_code = 'is' WHERE language_code IS NULL")
    op.execute("UPDATE cities SET language_code = 'is' WHERE language_code IS NULL")
    op.execute("UPDATE jobs SET language_code = 'is' WHERE language_code IS NULL")
    op.execute("UPDATE activities SET language_code = 'is' WHERE language_code IS NULL")
    op.execute("UPDATE topic SET language_code = 'is' WHERE language_code IS NULL")
    op.execute("UPDATE persons SET language_code = 'is' WHERE language_code IS NULL")

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info("Rolling back migration %s: Removing multi-language support", revision)

    # Remove foreign key and column from user_settings
    op.drop_constraint('fk_user_settings_target_language_id', 'user_settings', type_='foreignkey')
    op.drop_column('user_settings', 'target_language_id')

    # Remove language_code columns and indexes
    op.drop_index('ix_persons_language_code', 'persons')
    op.drop_column('persons', 'language_code')

    op.drop_index('ix_topic_language_code', 'topic')
    op.drop_column('topic', 'language_code')

    op.drop_index('ix_activities_language_code', 'activities')
    op.drop_column('activities', 'language_code')

    op.drop_index('ix_jobs_language_code', 'jobs')
    op.drop_column('jobs', 'language_code')

    op.drop_index('ix_cities_language_code', 'cities')
    op.drop_column('cities', 'language_code')

    op.drop_index('ix_names_language_code', 'names')
    op.drop_column('names', 'language_code')

    # Drop target_languages table
    op.drop_table('target_languages')

    logger.info("Migration %s rolled back successfully", revision)