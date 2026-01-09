"""
Module for fetching random topics from the database.

Supports multi-language filtering based on language_code.
"""
import logging
from sqlalchemy import func
from bot.db.database import db_session
from bot.db.models import Topic
from bot.languages import get_language_config, get_language_config_by_code

# Get logger for this module
logger = logging.getLogger(__name__)


def get_random_topic(language_code: str = None):
    """
    Fetch a random topic from the database.

    Args:
        language_code: ISO language code to filter topics (e.g., 'de', 'is').
                       If None, uses the default TARGET_LANGUAGE.

    Returns:
        str: A random topic name or None if no topics are found
    """
    # Determine which language to use
    if language_code:
        lang_config = get_language_config_by_code(language_code)
        if not lang_config:
            logger.warning(f"Unknown language code: {language_code}, falling back to default")
            lang_config = get_language_config()
            language_code = lang_config.code
    else:
        lang_config = get_language_config()
        language_code = lang_config.code

    logger.info(f"Fetching random topic from database for language: {language_code}")

    try:
        with db_session(auto_commit=False) as session:
            # Get a random topic (single query using func.random())
            topic = session.query(Topic).filter(
                Topic.language_code == language_code
            ).order_by(func.random()).limit(1).first()

            if not topic:
                logger.error(f"No topics found in database for language: {language_code}")
                return None

            logger.info(f"Successfully fetched random topic: {topic.name}")
            return topic.name
    except Exception as e:
        logger.error(f"Error fetching random topic: {e}")
        return None
