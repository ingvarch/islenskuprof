"""
User service module for database operations.
"""

import logging
from sqlalchemy.exc import SQLAlchemyError
import sqlalchemy.orm
from bot.db.database import db_session
from bot.db.models import (
    User,
    Language,
    UserSettings,
    AudioSpeed,
    LanguageLevel,
    TargetLanguage,
)

# Get logger for this module
logger = logging.getLogger(__name__)

# Constants
DEFAULT_AUDIO_SPEED_ID = 3  # Fallback ID for "Normal" speed


def _get_default_audio_speed_id(session):
    """Get the default audio speed ID, with fallback to constant."""
    audio_speed = (
        session.query(AudioSpeed).filter(AudioSpeed.description == "Normal").first()
    )
    return audio_speed.id if audio_speed else DEFAULT_AUDIO_SPEED_ID


def _get_or_create_user_settings(session, user_id, **kwargs):
    """
    Get existing user settings or create new ones.

    Args:
        session: Database session
        user_id: User ID
        **kwargs: Additional fields to set on new settings

    Returns:
        UserSettings: The user settings object
    """
    settings = (
        session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    )
    if settings:
        return settings

    # Create new settings with defaults
    default_audio_speed_id = _get_default_audio_speed_id(session)
    new_settings = UserSettings(
        user_id=user_id,
        audio_speed_id=default_audio_speed_id,
        language_id=None,
        **kwargs,
    )
    session.add(new_settings)
    return new_settings


def _update_user_setting(telegram_id, field_name, value, log_name=None):
    """
    Generic function to update a single user setting field.

    Args:
        telegram_id: Telegram user ID
        field_name: Name of the UserSettings field to update
        value: Value to set
        log_name: Human-readable name for logging (defaults to field_name)

    Returns:
        bool: True if updated successfully, False otherwise
    """
    log_name = log_name or field_name
    try:
        with db_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                logger.warning(f"User {telegram_id} not found for updating {log_name}")
                return False

            settings = _get_or_create_user_settings(session, user.id)
            setattr(settings, field_name, value)
            logger.info(f"Updated {log_name} for user {telegram_id} to {value}")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Error updating {log_name} for user {telegram_id}: {e}")
        return False


def get_or_create_user(
    telegram_id, username=None, first_name=None, last_name=None, is_premium=False
):
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
    try:
        with db_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()

            if user:
                # Update user information if changed
                updated = False
                if username and user.username != username:
                    user.username = username
                    updated = True
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                    updated = True
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                    updated = True
                if is_premium is not None and user.is_premium != is_premium:
                    user.is_premium = is_premium
                    updated = True

                if updated:
                    logger.info(f"Updated user information for user {telegram_id}")

                return user

            # Create new user
            english_language = (
                session.query(Language).filter(Language.code == "en").first()
            )
            if not english_language:
                logger.warning(
                    "English language not found in the database, creating it"
                )
                english_language = Language(code="en", language="English")
                session.add(english_language)
                session.flush()

            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_premium=is_premium,
            )
            session.add(user)
            session.flush()
            logger.info(f"Created new user with telegram_id {telegram_id}")

            # Get the default language level (A2)
            default_language_level = (
                session.query(LanguageLevel).filter(LanguageLevel.level == "A2").first()
            )
            default_language_level_id = (
                default_language_level.id if default_language_level else None
            )
            if not default_language_level:
                logger.warning("A2 language level not found in the database")

            # Create user settings with defaults
            _get_or_create_user_settings(
                session,
                user.id,
                language_id=english_language.id,
                language_level_id=default_language_level_id,
            )
            logger.info(
                f"Created user settings for new user {telegram_id} with default language"
            )

            return user
    except SQLAlchemyError as e:
        logger.error(f"Error getting or creating user: {e}")
        raise


def update_user_last_contact(telegram_id):
    """
    Update the last_contact timestamp for a user.

    Args:
        telegram_id: Telegram user ID

    Returns:
        bool: True if the user was updated, False otherwise
    """
    try:
        with db_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.update_last_contact()
                logger.info(f"Updated last_contact for user {telegram_id}")
                return True
            logger.warning(f"User {telegram_id} not found for updating last_contact")
            return False
    except SQLAlchemyError as e:
        logger.error(f"Error updating last_contact for user {telegram_id}: {e}")
        return False


def get_user_by_telegram_id(telegram_id):
    """
    Get a user by Telegram ID.

    Args:
        telegram_id: Telegram user ID

    Returns:
        User: The user object or None if not found
    """
    try:
        with db_session(auto_commit=False) as session:
            # Eagerly load relationships to avoid DetachedInstanceError
            user = (
                session.query(User)
                .options(
                    sqlalchemy.orm.joinedload(User.settings).joinedload(
                        UserSettings.language
                    ),
                    sqlalchemy.orm.joinedload(User.settings).joinedload(
                        UserSettings.audio_speed
                    ),
                    sqlalchemy.orm.joinedload(User.settings).joinedload(
                        UserSettings.language_level
                    ),
                    sqlalchemy.orm.joinedload(User.settings).joinedload(
                        UserSettings.target_language
                    ),
                )
                .filter(User.telegram_id == telegram_id)
                .first()
            )
            return user
    except SQLAlchemyError as e:
        logger.error(f"Error getting user by telegram_id {telegram_id}: {e}")
        return None


def update_user_language(telegram_id, language_id):
    """Update the language preference for a user."""
    return _update_user_setting(
        telegram_id, "language_id", language_id, "language preference"
    )


def _get_all(model, order_by=None, error_msg="Error getting records"):
    """
    Generic function to get all records from a table.

    Args:
        model: SQLAlchemy model class
        order_by: Optional column to order by
        error_msg: Error message prefix for logging

    Returns:
        list: List of model objects
    """
    try:
        with db_session(auto_commit=False) as session:
            query = session.query(model)
            if order_by is not None:
                query = query.order_by(order_by)
            return query.all()
    except SQLAlchemyError as e:
        logger.error(f"{error_msg}: {e}")
        return []


def get_all_languages():
    """Get all available languages."""
    return _get_all(Language, error_msg="Error getting all languages")


def get_all_audio_speeds():
    """Get all available audio speeds."""
    return _get_all(
        AudioSpeed, order_by=AudioSpeed.id, error_msg="Error getting all audio speeds"
    )


def get_all_language_levels():
    """Get all available language levels."""
    return _get_all(
        LanguageLevel,
        order_by=LanguageLevel.id,
        error_msg="Error getting all language levels",
    )


def update_user_audio_speed(telegram_id, audio_speed_id):
    """Update the audio speed setting for a user."""
    return _update_user_setting(
        telegram_id, "audio_speed_id", audio_speed_id, "audio speed"
    )


def get_user_audio_speed(telegram_id):
    """
    Get the audio speed setting for a user.

    Args:
        telegram_id: Telegram user ID

    Returns:
        float: The audio speed value or 1.0 if not found
    """
    try:
        with db_session(auto_commit=False) as session:
            # Single JOIN query instead of 3 sequential queries
            result = (
                session.query(AudioSpeed.speed)
                .join(UserSettings, AudioSpeed.id == UserSettings.audio_speed_id)
                .join(User, UserSettings.user_id == User.id)
                .filter(User.telegram_id == telegram_id)
                .first()
            )

            if result:
                return result[0]

            logger.warning(f"Audio speed not found for user {telegram_id}")
            return 1.0
    except SQLAlchemyError as e:
        logger.error(f"Error getting audio speed for user {telegram_id}: {e}")
        return 1.0


def update_user_language_level(telegram_id, language_level_id):
    """Update the language level setting for a user."""
    return _update_user_setting(
        telegram_id, "language_level_id", language_level_id, "language level"
    )


def update_user_last_section(telegram_id, section):
    """Update the last section shown to a user."""
    return _update_user_setting(telegram_id, "last_section", section, "last section")


def get_all_target_languages():
    """Get all available target languages for learning."""
    return _get_all(
        TargetLanguage,
        order_by=TargetLanguage.id,
        error_msg="Error getting all target languages",
    )


def get_target_language_by_id(target_language_id):
    """
    Get a target language by its ID.

    Args:
        target_language_id: ID of the target language

    Returns:
        TargetLanguage object or None if not found
    """
    try:
        with db_session(auto_commit=False) as session:
            return (
                session.query(TargetLanguage).filter_by(id=target_language_id).first()
            )
    except SQLAlchemyError as e:
        logger.error(f"Error getting target language by ID {target_language_id}: {e}")
        return None


def update_user_target_language(telegram_id, target_language_id):
    """Update the target language for a user."""
    return _update_user_setting(
        telegram_id, "target_language_id", target_language_id, "target language"
    )


def get_user_background_effects(telegram_id):
    """
    Get the background effects setting for a user.

    Args:
        telegram_id: Telegram user ID

    Returns:
        str: Background effects setting ("off", "auto", or preset ID)
    """
    try:
        with db_session(auto_commit=False) as session:
            # Single JOIN query instead of 2 sequential queries
            result = (
                session.query(UserSettings.background_effects)
                .join(User, UserSettings.user_id == User.id)
                .filter(User.telegram_id == telegram_id)
                .first()
            )

            if result and result[0]:
                return result[0]

            return "off"
    except SQLAlchemyError as e:
        logger.error(f"Error getting background effects for user {telegram_id}: {e}")
        return "off"


def update_user_background_effects(telegram_id, preset_value):
    """Update the background effects setting for a user."""
    return _update_user_setting(
        telegram_id, "background_effects", preset_value, "background effects"
    )
