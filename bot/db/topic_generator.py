"""
Module for fetching random topics from the database.
"""
import logging
import random
from sqlalchemy import func
from bot.db.database import get_db_session
from bot.db.models import Topic

# Get logger for this module
logger = logging.getLogger(__name__)

def get_random_topic():
    """
    Fetch a random topic from the database.

    Returns:
        str: A random topic name or None if no topics are found
    """
    logger.info("Fetching random topic from database")
    session = get_db_session()

    try:
        # Get a random topic from the database
        topic_count = session.query(func.count(Topic.id)).scalar()
        if topic_count == 0:
            logger.error("No topics found in database")
            return None

        random_offset = random.randint(0, topic_count - 1)
        topic = session.query(Topic).offset(random_offset).limit(1).first()

        if not topic:
            logger.error("Failed to fetch random topic")
            return None

        logger.info(f"Successfully fetched random topic: {topic.name}")
        return topic.name

    except Exception as e:
        logger.error(f"Error fetching random topic: {e}")
        return None
    finally:
        session.close()
