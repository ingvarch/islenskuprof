"""
User service module for database operations.
"""
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from bot.db.database import get_db_session
from bot.db.models import User

# Get logger for this module
logger = logging.getLogger(__name__)

def get_or_create_user(telegram_id, username=None, first_name=None, last_name=None, is_premium=False):
    """
    Get an existing user or create a new one if not exists.

    Args:
        telegram_id: Telegram user ID
        username: Telegram username
        first_name: User's first name
        last_name: User's last name
        is_premium: Whether the user has Telegram Premium

    Returns:
        User: The user object
    """
    session = get_db_session()
    try:
        # Try to get the user
        user = session.query(User).filter(User.telegram_id == telegram_id).first()

        if user:
            # Update user information if it has changed
            if (username and user.username != username) or \
               (first_name and user.first_name != first_name) or \
               (last_name and user.last_name != last_name) or \
               (is_premium is not None and user.is_premium != is_premium):
                user.username = username or user.username
                user.first_name = first_name or user.first_name
                user.last_name = last_name or user.last_name
                if is_premium is not None:
                    user.is_premium = is_premium
                session.commit()
                logger.info(f"Updated user information for user {telegram_id}")

            return user
        else:
            # Create a new user
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_premium=is_premium
            )
            session.add(user)
            session.commit()
            logger.info(f"Created new user with telegram_id {telegram_id}")
            return user
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error getting or creating user: {e}")
        raise
    finally:
        session.close()

def update_user_last_contact(telegram_id):
    """
    Update the last_contact timestamp for a user.

    Args:
        telegram_id: Telegram user ID

    Returns:
        bool: True if the user was updated, False otherwise
    """
    session = get_db_session()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.update_last_contact()
            session.commit()
            logger.info(f"Updated last_contact for user {telegram_id}")
            return True
        else:
            logger.warning(f"User {telegram_id} not found for updating last_contact")
            return False
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating last_contact for user {telegram_id}: {e}")
        return False
    finally:
        session.close()

def get_user_by_telegram_id(telegram_id):
    """
    Get a user by Telegram ID.

    Args:
        telegram_id: Telegram user ID

    Returns:
        User: The user object or None if not found
    """
    session = get_db_session()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error getting user by telegram_id {telegram_id}: {e}")
        return None
    finally:
        session.close()
