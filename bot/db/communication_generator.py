"""
Module for fetching random communication entries from the database.
"""
import logging
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from bot.db.database import db_session
from bot.db.models import Communication

# Get logger for this module
logger = logging.getLogger(__name__)


def get_random_communication():
    """
    Fetch a random communication entry from the database.

    Returns:
        dict: A dictionary containing the communication entry data or None if no entries are found
    """
    logger.info("Fetching random communication entry from database")

    try:
        with db_session(auto_commit=False) as session:
            # Get a random communication entry with topic eagerly loaded (single query)
            entry = session.query(Communication).options(
                joinedload(Communication.topic)
            ).order_by(func.random()).limit(1).first()

            if not entry:
                logger.error("No communication entries found in database")
                return None

            logger.info(f"Successfully fetched random communication entry: {entry.id}")

            # Return the entry data as a dictionary
            return {
                "id": entry.id,
                "topic_id": entry.topic_id,
                "topic_name": entry.topic.name if entry.topic else None,
                "image_url": entry.image_url,
                "description": entry.description
            }
    except Exception as e:
        logger.error(f"Error fetching random communication entry: {e}")
        return None
