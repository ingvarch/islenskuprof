"""
Database seeder module.

This module provides functions to seed database tables with language-specific data
based on the TARGET_LANGUAGES environment variable.

Supports multiple target languages simultaneously. Data is seeded with language_code
to enable per-user language selection.
"""

import logging
import sqlalchemy as sa
from sqlalchemy import func
from bot.db.database import db_session
from bot.db.models import Name, City, Job, Activity, Topic, TargetLanguage
from bot.languages import get_all_language_configs

logger = logging.getLogger(__name__)


def is_table_empty(session, model) -> bool:
    """
    Check if a database table is empty.

    Args:
        session: SQLAlchemy session
        model: SQLAlchemy model class

    Returns:
        True if the table is empty, False otherwise
    """
    return session.query(func.count(model.id)).scalar() == 0


def seed_names(session, names, language_code: str):
    """
    Seed the names table.

    Args:
        session: SQLAlchemy session
        names: List of (first_name, last_name) tuples
        language_code: ISO language code (e.g., 'de', 'is')
    """
    for first_name, last_name in names:
        session.add(
            Name(
                first_name=first_name, last_name=last_name, language_code=language_code
            )
        )
    logger.info(f"Added {len(names)} names for {language_code} to database")


def seed_cities(session, cities, language_code: str):
    """
    Seed the cities table.

    Args:
        session: SQLAlchemy session
        cities: List of city names
        language_code: ISO language code (e.g., 'de', 'is')
    """
    for city_name in cities:
        session.add(City(name=city_name, language_code=language_code))
    logger.info(f"Added {len(cities)} cities for {language_code} to database")


def seed_jobs(session, jobs, language_code: str):
    """
    Seed the jobs table.

    Args:
        session: SQLAlchemy session
        jobs: List of (title, workplace) tuples
        language_code: ISO language code (e.g., 'de', 'is')
    """
    for title, workplace in jobs:
        session.add(Job(title=title, workplace=workplace, language_code=language_code))
    logger.info(f"Added {len(jobs)} jobs for {language_code} to database")


def seed_activities(session, weekend_activities, plan_activities, language_code: str):
    """
    Seed the activities table.

    Args:
        session: SQLAlchemy session
        weekend_activities: List of weekend activity descriptions
        plan_activities: List of plan activity descriptions
        language_code: ISO language code (e.g., 'de', 'is')
    """
    for activity in weekend_activities:
        session.add(
            Activity(activity=activity, type="weekend", language_code=language_code)
        )
    for activity in plan_activities:
        session.add(
            Activity(activity=activity, type="plan", language_code=language_code)
        )
    total = len(weekend_activities) + len(plan_activities)
    logger.info(f"Added {total} activities for {language_code} to database")


def seed_topics(session, topics, language_code: str):
    """
    Seed the topics table.

    Args:
        session: SQLAlchemy session
        topics: List of topic names
        language_code: ISO language code (e.g., 'de', 'is')
    """
    for topic_name in topics:
        session.add(Topic(name=topic_name, language_code=language_code))
    logger.info(f"Added {len(topics)} topics for {language_code} to database")


def reset_sequences(session):
    """
    Reset PostgreSQL sequences to match the current max IDs in tables.
    This is needed when data was inserted without using sequences.
    """
    # Whitelist of allowed table names to prevent SQL injection
    ALLOWED_TABLES = frozenset(
        [
            "names",
            "cities",
            "jobs",
            "activities",
            "topic",
            "persons",
            "target_languages",
        ]
    )

    for table in ALLOWED_TABLES:
        try:
            # Using text() with explicit table validation for safety
            session.execute(
                sa.text(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table}"
                )
            )
            logger.debug(f"Reset sequence for table {table}")
        except Exception as e:
            logger.warning(f"Could not reset sequence for {table}: {e}")
    session.commit()


def seed_target_languages(session, lang_configs):
    """
    Seed the target_languages table with available languages.

    Args:
        session: SQLAlchemy session
        lang_configs: List of LanguageConfig instances
    """
    for lang_config in lang_configs:
        existing = (
            session.query(TargetLanguage).filter_by(code=lang_config.code).first()
        )
        if not existing:
            session.add(
                TargetLanguage(
                    code=lang_config.code,
                    name=lang_config.name,
                    native_name=lang_config.native_name,
                )
            )
            logger.info(
                f"Added target language: {lang_config.name} ({lang_config.code})"
            )


def has_language_data(session, model, language_code: str) -> bool:
    """
    Check if a table has data for a specific language.

    Args:
        session: SQLAlchemy session
        model: SQLAlchemy model class
        language_code: ISO language code

    Returns:
        True if data exists for this language, False otherwise
    """
    return (
        session.query(func.count(model.id))
        .filter_by(language_code=language_code)
        .scalar()
        > 0
    )


def seed_database_if_empty():
    """
    Check if seed data tables need data and populate them if needed.

    Uses TARGET_LANGUAGES environment variable (comma-separated list of language codes).
    Seeds data for all configured languages.
    This function is idempotent - it will only seed data that doesn't exist.
    """
    lang_configs = get_all_language_configs()

    if not lang_configs:
        logger.warning("No target languages configured. Set TARGET_LANGUAGES env var.")
        return

    language_names = [lc.name for lc in lang_configs]
    logger.info(f"Checking if database needs seeding for: {', '.join(language_names)}")

    try:
        with db_session() as session:
            # Reset sequences to avoid primary key conflicts
            reset_sequences(session)

            # Seed target_languages table first
            seed_target_languages(session, lang_configs)

            # Seed data for each configured language
            for lang_config in lang_configs:
                code = lang_config.code
                seed_data = lang_config.seed_data
                tables_seeded = []

                if not has_language_data(session, Name, code):
                    seed_names(session, seed_data.names, code)
                    tables_seeded.append("names")

                if not has_language_data(session, City, code):
                    seed_cities(session, seed_data.cities, code)
                    tables_seeded.append("cities")

                if not has_language_data(session, Job, code):
                    seed_jobs(session, seed_data.jobs, code)
                    tables_seeded.append("jobs")

                if not has_language_data(session, Activity, code):
                    seed_activities(
                        session,
                        seed_data.weekend_activities,
                        seed_data.plan_activities,
                        code,
                    )
                    tables_seeded.append("activities")

                if not has_language_data(session, Topic, code):
                    seed_topics(session, seed_data.topics, code)
                    tables_seeded.append("topics")

                if tables_seeded:
                    logger.info(
                        f"Seeded tables for {lang_config.name}: {', '.join(tables_seeded)}"
                    )
                else:
                    logger.info(
                        f"All seed data tables already populated for {lang_config.name}"
                    )

            logger.info("Database seeding completed successfully")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        raise


def clear_and_reseed_database():
    """
    Clear all seed data tables and reseed them with current language configurations.

    WARNING: This will delete all existing data in the seed tables!
    Use with caution - primarily for testing or resetting data.
    """
    lang_configs = get_all_language_configs()

    if not lang_configs:
        logger.warning("No target languages configured. Set TARGET_LANGUAGES env var.")
        return

    language_names = [lc.name for lc in lang_configs]
    logger.warning(
        f"Clearing and reseeding database for: {', '.join(language_names)}..."
    )

    try:
        with db_session() as session:
            # Clear existing data
            session.query(Name).delete()
            session.query(City).delete()
            session.query(Job).delete()
            session.query(Activity).delete()
            session.query(Topic).delete()
            session.query(TargetLanguage).delete()

            # Seed target_languages table
            seed_target_languages(session, lang_configs)

            # Seed data for each language
            for lang_config in lang_configs:
                code = lang_config.code
                seed_data = lang_config.seed_data

                seed_names(session, seed_data.names, code)
                seed_cities(session, seed_data.cities, code)
                seed_jobs(session, seed_data.jobs, code)
                seed_activities(
                    session,
                    seed_data.weekend_activities,
                    seed_data.plan_activities,
                    code,
                )
                seed_topics(session, seed_data.topics, code)

            logger.info(
                f"Database cleared and reseeded for: {', '.join(language_names)}"
            )
    except Exception as e:
        logger.error(f"Error clearing and reseeding database: {e}")
        raise
