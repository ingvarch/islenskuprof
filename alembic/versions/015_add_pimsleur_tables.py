"""Add Pimsleur method tables for lesson storage and user progress

Revision ID: 015
Revises: 014
Create Date: 2026-01-07

"""

from alembic import op
import sqlalchemy as sa
import logging

# Get logger
logger = logging.getLogger("alembic.runtime.migration")

# revision identifiers, used by Alembic.
revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade():
    logger.info("Applying migration %s: Adding Pimsleur method tables", revision)

    # 1. Create pimsleur_lessons table - stores lesson metadata and audio
    op.create_table(
        "pimsleur_lessons",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("language_code", sa.String(10), nullable=False, index=True),
        sa.Column("level", sa.String(5), nullable=False),
        sa.Column("lesson_number", sa.Integer, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=False, default=1800),
        sa.Column("audio_file_path", sa.String(500), nullable=True),
        sa.Column("telegram_file_id", sa.String(255), nullable=True),
        sa.Column("script_json", sa.Text, nullable=False),
        sa.Column("vocabulary_json", sa.Text, nullable=False),
        sa.Column("review_from_lessons", sa.Text, nullable=True),
        sa.Column("is_generated", sa.Boolean, nullable=False, default=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "language_code", "level", "lesson_number", name="uq_pimsleur_lesson"
        ),
    )
    logger.info("Created pimsleur_lessons table")

    # 2. Create pimsleur_vocabulary table - master vocabulary tracking
    op.create_table(
        "pimsleur_vocabulary",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("language_code", sa.String(10), nullable=False, index=True),
        sa.Column("word_target", sa.String(255), nullable=False),
        sa.Column("word_native", sa.String(255), nullable=False),
        sa.Column("phonetic", sa.String(255), nullable=True),
        sa.Column("word_type", sa.String(50), nullable=True),
        sa.Column("cefr_level", sa.String(5), nullable=False),
        sa.Column(
            "introduced_lesson_id",
            sa.Integer,
            sa.ForeignKey("pimsleur_lessons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("frequency_rank", sa.Integer, nullable=True),
        sa.Column("audio_file_path", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "language_code", "word_target", name="uq_pimsleur_vocab_word"
        ),
    )
    logger.info("Created pimsleur_vocabulary table")

    # 3. Create pimsleur_lesson_vocabulary junction table
    op.create_table(
        "pimsleur_lesson_vocabulary",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "lesson_id",
            sa.Integer,
            sa.ForeignKey("pimsleur_lessons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vocabulary_id",
            sa.Integer,
            sa.ForeignKey("pimsleur_vocabulary.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_new", sa.Boolean, nullable=False, default=False),
        sa.Column("repetition_count", sa.Integer, nullable=False, default=0),
        sa.Column("intervals_json", sa.Text, nullable=True),
        sa.UniqueConstraint("lesson_id", "vocabulary_id", name="uq_lesson_vocab"),
    )
    logger.info("Created pimsleur_lesson_vocabulary table")

    # 4. Create user_pimsleur_progress table
    op.create_table(
        "user_pimsleur_progress",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("language_code", sa.String(10), nullable=False),
        sa.Column("level", sa.String(5), nullable=False, default="A1"),
        sa.Column("lesson_number", sa.Integer, nullable=False, default=1),
        sa.Column("completed_lessons", sa.Text, nullable=True),
        sa.Column(
            "last_lesson_id",
            sa.Integer,
            sa.ForeignKey("pimsleur_lessons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("last_completed_at", sa.DateTime, nullable=True),
        sa.Column("streak_count", sa.Integer, nullable=False, default=0),
        sa.Column("total_time_seconds", sa.Integer, nullable=False, default=0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id", "language_code", name="uq_user_pimsleur_progress"
        ),
    )
    logger.info("Created user_pimsleur_progress table")

    # 5. Create pimsleur_custom_lessons table
    op.create_table(
        "pimsleur_custom_lessons",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("language_code", sa.String(10), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_text", sa.Text, nullable=False),
        sa.Column("script_json", sa.Text, nullable=True),
        sa.Column("audio_file_path", sa.String(500), nullable=True),
        sa.Column("telegram_file_id", sa.String(255), nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
        sa.Column("vocabulary_json", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, default="pending"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    logger.info("Created pimsleur_custom_lessons table")

    # Create indexes for faster lookups
    op.create_index(
        "ix_pimsleur_lessons_lookup",
        "pimsleur_lessons",
        ["language_code", "level", "lesson_number"],
    )
    op.create_index(
        "ix_user_pimsleur_progress_user",
        "user_pimsleur_progress",
        ["user_id", "language_code"],
    )
    op.create_index(
        "ix_pimsleur_custom_lessons_user",
        "pimsleur_custom_lessons",
        ["user_id", "status"],
    )

    logger.info("Migration %s applied successfully", revision)


def downgrade():
    logger.info("Rolling back migration %s: Removing Pimsleur method tables", revision)

    # Drop indexes
    op.drop_index(
        "ix_pimsleur_custom_lessons_user", table_name="pimsleur_custom_lessons"
    )
    op.drop_index("ix_user_pimsleur_progress_user", table_name="user_pimsleur_progress")
    op.drop_index("ix_pimsleur_lessons_lookup", table_name="pimsleur_lessons")

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("pimsleur_custom_lessons")
    op.drop_table("user_pimsleur_progress")
    op.drop_table("pimsleur_lesson_vocabulary")
    op.drop_table("pimsleur_vocabulary")
    op.drop_table("pimsleur_lessons")

    logger.info("Migration %s rolled back successfully", revision)
