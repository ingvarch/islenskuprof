"""Seed languages and update users

Revision ID: 006
Revises: 005
Create Date: 2023-12-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
import logging

# Get logger
logger = logging.getLogger('alembic.runtime.migration')

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Applying migration %s: Seeding languages and updating users", revision)

    connection = op.get_bind()
    
    # Insert English and Russian languages
    connection.execute(
        text("INSERT INTO languages (code, language) VALUES ('en', 'English'), ('ru', 'Russian')")
    )
    
    # Get the ID of English language
    result = connection.execute(text("SELECT id FROM languages WHERE code = 'en'"))
    english_id = result.fetchone()[0]
    
    # Set English as default language for all existing users
    connection.execute(
        text(f"UPDATE users SET language_id = {english_id}")
    )
    
    # Make language_id not nullable after setting default values
    op.alter_column('users', 'language_id', nullable=False)

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info("Rolling back migration %s: Reverting user language settings", revision)

    # Make language_id nullable again
    op.alter_column('users', 'language_id', nullable=True)
    
    # Set language_id to NULL for all users
    connection = op.get_bind()
    connection.execute(text("UPDATE users SET language_id = NULL"))
    
    # Delete all languages
    connection.execute(text("DELETE FROM languages"))

    logger.info("Migration %s rolled back successfully", revision)
