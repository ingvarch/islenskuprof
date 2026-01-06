"""
User service module for database operations.
"""
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import sqlalchemy.orm
from bot.db.database import get_db_session
from bot.db.models import User, Language, UserSettings, AudioSpeed, LanguageLevel, TargetLanguage

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
            # Get the English language ID (default)
            english_language = session.query(Language).filter(Language.code == 'en').first()
            if not english_language:
                logger.warning("English language not found in the database, this should not happen")
                # If English language is not found, we'll create it
                english_language = Language(code='en', language='English')
                session.add(english_language)
                session.commit()

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

            # Get the default audio speed (Normal)
            default_audio_speed = session.query(AudioSpeed).filter(AudioSpeed.description == "Normal").first()
            if not default_audio_speed:
                default_audio_speed_id = 3  # Fallback to ID 3 if not found
            else:
                default_audio_speed_id = default_audio_speed.id

            # Get the default language level (A2)
            default_language_level = session.query(LanguageLevel).filter(LanguageLevel.level == "A2").first()
            if not default_language_level:
                logger.warning("A2 language level not found in the database, this should not happen")
                # If A2 language level is not found, we'll use None
                default_language_level_id = None
            else:
                default_language_level_id = default_language_level.id

            # Create user settings with default language and language level
            user_settings = UserSettings(
                user_id=user.id,
                audio_speed_id=default_audio_speed_id,
                language_id=english_language.id,
                language_level_id=default_language_level_id
            )
            session.add(user_settings)
            session.commit()
            logger.info(f"Created user settings for new user {telegram_id} with default language")

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
        # Eagerly load the settings relationship and its language, audio_speed, and language_level to avoid DetachedInstanceError
        user = session.query(User).options(
            sqlalchemy.orm.joinedload(User.settings).joinedload(UserSettings.language),
            sqlalchemy.orm.joinedload(User.settings).joinedload(UserSettings.audio_speed),
            sqlalchemy.orm.joinedload(User.settings).joinedload(UserSettings.language_level)
        ).filter(User.telegram_id == telegram_id).first()

        # User settings, language, and audio_speed are already loaded through the joinedload above

        return user
    except SQLAlchemyError as e:
        logger.error(f"Error getting user by telegram_id {telegram_id}: {e}")
        return None
    finally:
        session.close()

def update_user_language(telegram_id, language_id):
    """
    Update the language preference for a user in the user_settings table.

    Args:
        telegram_id: Telegram user ID
        language_id: ID of the language to set

    Returns:
        bool: True if the user settings were updated, False otherwise
    """
    session = get_db_session()
    try:
        # Get the user by telegram_id
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            logger.warning(f"User {telegram_id} not found for updating language preference")
            return False

        # Check if user has settings
        user_settings = session.query(UserSettings).filter(UserSettings.user_id == user.id).first()

        if user_settings:
            # Update existing settings
            user_settings.language_id = language_id
            session.commit()
            logger.info(f"Updated language preference for user {telegram_id} to language_id {language_id}")
            return True
        else:
            # Create new settings with default audio_speed_id=3 (Normal)
            # Get the default audio speed (Normal)
            default_audio_speed = session.query(AudioSpeed).filter(AudioSpeed.description == "Normal").first()
            if not default_audio_speed:
                default_audio_speed_id = 3  # Fallback to ID 3 if not found
            else:
                default_audio_speed_id = default_audio_speed.id

            # Create new user settings
            new_settings = UserSettings(
                user_id=user.id,
                audio_speed_id=default_audio_speed_id,
                language_id=language_id
            )
            session.add(new_settings)
            session.commit()
            logger.info(f"Created new settings with language preference for user {telegram_id} to language_id {language_id}")
            return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating language preference for user {telegram_id}: {e}")
        return False
    finally:
        session.close()

def get_all_languages():
    """
    Get all available languages.

    Returns:
        list: List of Language objects
    """
    session = get_db_session()
    try:
        languages = session.query(Language).all()
        return languages
    except SQLAlchemyError as e:
        logger.error(f"Error getting all languages: {e}")
        return []
    finally:
        session.close()

def get_all_audio_speeds():
    """
    Get all available audio speeds.

    Returns:
        list: List of AudioSpeed objects
    """
    session = get_db_session()
    try:
        audio_speeds = session.query(AudioSpeed).order_by(AudioSpeed.id).all()
        return audio_speeds
    except SQLAlchemyError as e:
        logger.error(f"Error getting all audio speeds: {e}")
        return []
    finally:
        session.close()


def get_all_language_levels():
    """
    Get all available language levels.

    Returns:
        list: List of LanguageLevel objects
    """
    session = get_db_session()
    try:
        language_levels = session.query(LanguageLevel).order_by(LanguageLevel.id).all()
        return language_levels
    except SQLAlchemyError as e:
        logger.error(f"Error getting all language levels: {e}")
        return []
    finally:
        session.close()

def update_user_audio_speed(telegram_id, audio_speed_id):
    """
    Update the audio speed setting for a user in the user_settings table.

    Args:
        telegram_id: Telegram user ID
        audio_speed_id: ID of the audio speed to set

    Returns:
        bool: True if the user settings were updated, False otherwise
    """
    session = get_db_session()
    try:
        # Get the user by telegram_id
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            logger.warning(f"User {telegram_id} not found for updating audio speed")
            return False

        # Check if user has settings
        user_settings = session.query(UserSettings).filter(UserSettings.user_id == user.id).first()

        if user_settings:
            # Update existing settings
            user_settings.audio_speed_id = audio_speed_id
            session.commit()
            logger.info(f"Updated audio speed for user {telegram_id} to audio_speed_id {audio_speed_id}")
            return True
        else:
            # Create new settings with default language_id=None
            new_settings = UserSettings(
                user_id=user.id,
                audio_speed_id=audio_speed_id,
                language_id=None
            )
            session.add(new_settings)
            session.commit()
            logger.info(f"Created new settings with audio speed for user {telegram_id} to audio_speed_id {audio_speed_id}")
            return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating audio speed for user {telegram_id}: {e}")
        return False
    finally:
        session.close()

def get_user_audio_speed(telegram_id):
    """
    Get the audio speed setting for a user.

    Args:
        telegram_id: Telegram user ID

    Returns:
        float: The audio speed value or 1.0 if not found
    """
    session = get_db_session()
    try:
        # Get the user by telegram_id
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            logger.warning(f"User {telegram_id} not found for getting audio speed")
            return 1.0  # Default speed if user not found

        # Get the user settings
        user_settings = session.query(UserSettings).filter(UserSettings.user_id == user.id).first()
        if not user_settings:
            logger.warning(f"User settings not found for user {telegram_id}")
            return 1.0  # Default speed if settings not found

        # Get the audio speed
        audio_speed = session.query(AudioSpeed).filter(AudioSpeed.id == user_settings.audio_speed_id).first()
        if not audio_speed:
            logger.warning(f"Audio speed not found for user settings {user_settings.id}")
            return 1.0  # Default speed if audio speed not found

        return audio_speed.speed
    except SQLAlchemyError as e:
        logger.error(f"Error getting audio speed for user {telegram_id}: {e}")
        return 1.0  # Default speed on error
    finally:
        session.close()


def update_user_language_level(telegram_id, language_level_id):
    """
    Update the language level setting for a user in the user_settings table.

    Args:
        telegram_id: Telegram user ID
        language_level_id: ID of the language level to set

    Returns:
        bool: True if the user settings were updated, False otherwise
    """
    session = get_db_session()
    try:
        # Get the user by telegram_id
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            logger.warning(f"User {telegram_id} not found for updating language level")
            return False

        # Check if user has settings
        user_settings = session.query(UserSettings).filter(UserSettings.user_id == user.id).first()

        if user_settings:
            # Update existing settings
            user_settings.language_level_id = language_level_id
            session.commit()
            logger.info(f"Updated language level for user {telegram_id} to language_level_id {language_level_id}")
            return True
        else:
            # Create new settings with default audio_speed_id and language_id=None
            # Get the default audio speed (Normal)
            default_audio_speed = session.query(AudioSpeed).filter(AudioSpeed.description == "Normal").first()
            if not default_audio_speed:
                default_audio_speed_id = 3  # Fallback to ID 3 if not found
            else:
                default_audio_speed_id = default_audio_speed.id

            # Create new user settings
            new_settings = UserSettings(
                user_id=user.id,
                audio_speed_id=default_audio_speed_id,
                language_id=None,
                language_level_id=language_level_id
            )
            session.add(new_settings)
            session.commit()
            logger.info(f"Created new settings with language level for user {telegram_id} to language_level_id {language_level_id}")
            return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating language level for user {telegram_id}: {e}")
        return False
    finally:
        session.close()


def update_user_last_section(telegram_id, section):
    """
    Update the last section shown to a user in the user_settings table.

    Args:
        telegram_id: Telegram user ID
        section: Section name ('listening' or 'reading')

    Returns:
        bool: True if the user settings were updated, False otherwise
    """
    session = get_db_session()
    try:
        # Get the user by telegram_id
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            logger.warning(f"User {telegram_id} not found for updating last section")
            return False

        # Check if user has settings
        user_settings = session.query(UserSettings).filter(UserSettings.user_id == user.id).first()

        if user_settings:
            # Update existing settings
            user_settings.last_section = section
            session.commit()
            logger.info(f"Updated last section for user {telegram_id} to {section}")
            return True
        else:
            # Create new settings with default audio_speed_id and language_id=None
            # Get the default audio speed (Normal)
            default_audio_speed = session.query(AudioSpeed).filter(AudioSpeed.description == "Normal").first()
            if not default_audio_speed:
                default_audio_speed_id = 3  # Fallback to ID 3 if not found
            else:
                default_audio_speed_id = default_audio_speed.id

            # Create new user settings
            new_settings = UserSettings(
                user_id=user.id,
                audio_speed_id=default_audio_speed_id,
                language_id=None,
                last_section=section
            )
            session.add(new_settings)
            session.commit()
            logger.info(f"Created new settings with last section for user {telegram_id} to {section}")
            return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating last section for user {telegram_id}: {e}")
        return False
    finally:
        session.close()


def get_all_target_languages():
    """
    Get all available target languages for learning.

    Returns:
        list: List of TargetLanguage objects
    """
    session = get_db_session()
    try:
        target_languages = session.query(TargetLanguage).order_by(TargetLanguage.id).all()
        return target_languages
    except SQLAlchemyError as e:
        logger.error(f"Error getting all target languages: {e}")
        return []
    finally:
        session.close()


def get_target_language_by_id(target_language_id):
    """
    Get a target language by its ID.

    Args:
        target_language_id: ID of the target language

    Returns:
        TargetLanguage object or None if not found
    """
    session = get_db_session()
    try:
        return session.query(TargetLanguage).filter_by(id=target_language_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error getting target language by ID {target_language_id}: {e}")
        return None
    finally:
        session.close()


def update_user_target_language(telegram_id, target_language_id):
    """
    Update the target language (language to learn) for a user in the user_settings table.

    Args:
        telegram_id: Telegram user ID
        target_language_id: ID of the target language to set

    Returns:
        bool: True if the user settings were updated, False otherwise
    """
    session = get_db_session()
    try:
        # Get the user by telegram_id
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            logger.warning(f"User {telegram_id} not found for updating target language")
            return False

        # Check if user has settings
        user_settings = session.query(UserSettings).filter(UserSettings.user_id == user.id).first()

        if user_settings:
            # Update existing settings
            user_settings.target_language_id = target_language_id
            session.commit()
            logger.info(f"Updated target language for user {telegram_id} to target_language_id {target_language_id}")
            return True
        else:
            # Create new settings with default audio_speed_id and language_id=None
            # Get the default audio speed (Normal)
            default_audio_speed = session.query(AudioSpeed).filter(AudioSpeed.description == "Normal").first()
            if not default_audio_speed:
                default_audio_speed_id = 3  # Fallback to ID 3 if not found
            else:
                default_audio_speed_id = default_audio_speed.id

            # Create new user settings
            new_settings = UserSettings(
                user_id=user.id,
                audio_speed_id=default_audio_speed_id,
                language_id=None,
                target_language_id=target_language_id
            )
            session.add(new_settings)
            session.commit()
            logger.info(f"Created new settings with target language for user {telegram_id} to target_language_id {target_language_id}")
            return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating target language for user {telegram_id}: {e}")
        return False
    finally:
        session.close()


def get_user_background_effects(telegram_id):
    """
    Get the background effects setting for a user.

    Args:
        telegram_id: Telegram user ID

    Returns:
        bool: True if background effects are enabled, False otherwise
    """
    session = get_db_session()
    try:
        # Get the user by telegram_id
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            logger.warning(f"User {telegram_id} not found for getting background effects")
            return False  # Default to disabled

        # Get the user settings
        user_settings = session.query(UserSettings).filter(UserSettings.user_id == user.id).first()
        if not user_settings:
            logger.warning(f"User settings not found for user {telegram_id}")
            return False  # Default to disabled

        return user_settings.background_effects
    except SQLAlchemyError as e:
        logger.error(f"Error getting background effects for user {telegram_id}: {e}")
        return False  # Default to disabled on error
    finally:
        session.close()


def update_user_background_effects(telegram_id, enabled):
    """
    Update the background effects setting for a user in the user_settings table.

    Args:
        telegram_id: Telegram user ID
        enabled: Whether to enable background effects

    Returns:
        bool: True if the user settings were updated, False otherwise
    """
    session = get_db_session()
    try:
        # Get the user by telegram_id
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            logger.warning(f"User {telegram_id} not found for updating background effects")
            return False

        # Check if user has settings
        user_settings = session.query(UserSettings).filter(UserSettings.user_id == user.id).first()

        if user_settings:
            # Update existing settings
            user_settings.background_effects = enabled
            session.commit()
            logger.info(f"Updated background effects for user {telegram_id} to {enabled}")
            return True
        else:
            # Create new settings with default audio_speed_id
            default_audio_speed = session.query(AudioSpeed).filter(AudioSpeed.description == "Normal").first()
            if not default_audio_speed:
                default_audio_speed_id = 3  # Fallback to ID 3 if not found
            else:
                default_audio_speed_id = default_audio_speed.id

            # Create new user settings
            new_settings = UserSettings(
                user_id=user.id,
                audio_speed_id=default_audio_speed_id,
                language_id=None,
                background_effects=enabled
            )
            session.add(new_settings)
            session.commit()
            logger.info(f"Created new settings with background effects for user {telegram_id} to {enabled}")
            return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating background effects for user {telegram_id}: {e}")
        return False
    finally:
        session.close()
