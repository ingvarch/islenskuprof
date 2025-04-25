"""
Module for fetching random communication entries from the database.
"""
import logging
import random
from sqlalchemy import func
from bot.db.database import get_db_session
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
    session = get_db_session()

    try:
        # Get a random communication entry from the database
        entry_count = session.query(func.count(Communication.id)).scalar()
        if entry_count == 0:
            logger.error("No communication entries found in database")
            return None

        random_offset = random.randint(0, entry_count - 1)
        entry = session.query(Communication).offset(random_offset).limit(1).first()

        if not entry:
            logger.error("Failed to fetch random communication entry")
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
    finally:
        session.close()
