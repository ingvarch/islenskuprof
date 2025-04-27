"""
Settings handlers module for the Telegram bot.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

from bot.utils.access_control import restricted
from bot.utils.user_tracking import track_user_activity
from bot.utils.message_cleaner import delete_user_command_message
from bot.db.user_service import (
    get_user_by_telegram_id, update_user_language, get_all_languages,
    get_all_audio_speeds, update_user_audio_speed,
    get_all_language_levels, update_user_language_level
)

# Get logger for this module
logger = logging.getLogger(__name__)

# Callback data prefixes
LANGUAGE_PREFIX = "lang_"
LANGUAGE_MENU = "lang_menu"
LANGUAGE_SELECT_PREFIX = "lang_select_"

# Audio speed callback data prefixes
AUDIO_SPEED_PREFIX = "speed_"
AUDIO_SPEED_MENU = "speed_menu"
AUDIO_SPEED_SELECT_PREFIX = "speed_select_"

# Language level callback data prefixes
LANGUAGE_LEVEL_PREFIX = "level_"
LANGUAGE_LEVEL_MENU = "level_menu"
LANGUAGE_LEVEL_SELECT_PREFIX = "level_select_"

@restricted
@track_user_activity
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send settings menu when the command /settings is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} requested settings menu")

    # Create keyboard with language, language level, and voice speed buttons
    keyboard = [
        [InlineKeyboardButton("Language", callback_data=LANGUAGE_MENU)],
        [InlineKeyboardButton("Language Level", callback_data=LANGUAGE_LEVEL_MENU)],
        [InlineKeyboardButton("Voice Speed", callback_data=AUDIO_SPEED_MENU)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    logger.info(f"Creating settings keyboard with language, language level, and voice speed buttons")

    # Send message with inline keyboard
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Settings",
        reply_markup=reply_markup
    )
    logger.info(f"Settings menu sent to user {user.id}")

    # Delete the user's command message
    await delete_user_command_message(update, context)

async def language_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the language menu button callback."""
    query = update.callback_query
    user = update.effective_user
    logger.info(f"LANGUAGE MENU CALLBACK ENTERED for user {user.id}")

    # Get all available languages
    languages = get_all_languages()
    logger.info(f"Retrieved {len(languages)} languages from database")

    if not languages:
        logger.error("No languages found in database. Make sure migrations have been run.")
        await query.answer(text="No languages available")
        await query.edit_message_text(
            text="Error: No languages available. Please contact the administrator."
        )
        return

    # Create keyboard with language buttons
    keyboard = []
    for language in languages:
        # Add flag emoji based on language code
        flag = "🇷🇺" if language.code == "ru" else "🇬🇧"
        button_text = f"{language.language} {flag}"
        callback_data = f"{LANGUAGE_SELECT_PREFIX}{language.id}"
        logger.info(f"Adding language button: {button_text} with callback_data: {callback_data}")
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=callback_data
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)
    logger.info(f"Created language selection keyboard with {len(languages)} buttons")

    # First answer the callback query
    await query.answer()

    # Then edit message to show language selection
    try:
        await query.edit_message_text(
            text="Select your preferred language:",
            reply_markup=reply_markup
        )
        logger.info(f"Successfully edited message to show language selection for user {user.id}")
    except Exception as e:
        logger.error(f"Error editing message: {e}", exc_info=True)

async def language_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the language selection callback."""
    query = update.callback_query
    user = update.effective_user
    logger.info(f"LANGUAGE SELECT CALLBACK ENTERED for user {user.id} with data: {query.data}")

    language_id = int(query.data.replace(LANGUAGE_SELECT_PREFIX, ""))
    logger.info(f"Parsed language_id: {language_id}")

    # First answer the callback query
    await query.answer()

    # Update user's language preference
    success = update_user_language(user.id, language_id)

    if success:
        # Get the selected language
        db_user = get_user_by_telegram_id(user.id)

        # Get language from user_settings
        if hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
            language_name = db_user.settings.language.language
            language_code = db_user.settings.language.code
        else:
            # Default to English if no settings or language available
            language_name = "English"
            language_code = "en"

        # Add flag emoji based on language code
        flag = "🇷🇺" if language_code == "ru" else "🇬🇧"

        # Confirmation message based on language
        if language_code == "ru":
            message = f"Вы выбрали Русский язык {flag}"
        else:
            message = f"You have selected English language {flag}"

        logger.info(f"User {user.id} selected language: {language_name}")

        # Edit message to show confirmation
        try:
            await query.edit_message_text(text=message)
            logger.info(f"Successfully updated message with confirmation for user {user.id}")
        except Exception as e:
            logger.error(f"Error editing message: {e}", exc_info=True)
    else:
        logger.error(f"Failed to update language preference for user {user.id}")
        try:
            await query.edit_message_text(text="Failed to update language preference. Please try again.")
        except Exception as e:
            logger.error(f"Error editing message: {e}", exc_info=True)

async def audio_speed_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the audio speed menu button callback."""
    query = update.callback_query
    user = update.effective_user
    logger.info(f"AUDIO SPEED MENU CALLBACK ENTERED for user {user.id}")

    # Get all available audio speeds
    audio_speeds = get_all_audio_speeds()
    logger.info(f"Retrieved {len(audio_speeds)} audio speeds from database")

    if not audio_speeds:
        logger.error("No audio speeds found in database. Make sure migrations have been run.")
        await query.answer(text="No audio speeds available")
        await query.edit_message_text(
            text="Error: No audio speeds available. Please contact the administrator."
        )
        return

    # Get the user's current audio speed setting
    db_user = get_user_by_telegram_id(user.id)
    current_audio_speed_id = None
    if hasattr(db_user, 'settings') and db_user.settings and db_user.settings.audio_speed:
        current_audio_speed_id = db_user.settings.audio_speed.id
        logger.info(f"User {user.id} current audio speed ID: {current_audio_speed_id}")

    # Create keyboard with audio speed buttons (2 buttons per row)
    keyboard = []
    current_row = []

    for audio_speed in audio_speeds:
        # Add green checkmark to the current speed
        if current_audio_speed_id and audio_speed.id == current_audio_speed_id:
            button_text = f"{audio_speed.description} ✅"
        else:
            button_text = f"{audio_speed.description}"

        callback_data = f"{AUDIO_SPEED_SELECT_PREFIX}{audio_speed.id}"
        logger.info(f"Adding audio speed button: {button_text} with callback_data: {callback_data}")

        # Add button to current row
        current_row.append(InlineKeyboardButton(
            button_text,
            callback_data=callback_data
        ))

        # If we have 2 buttons in the current row, add it to the keyboard and start a new row
        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []

    # Add any remaining buttons (in case of odd number of buttons)
    if current_row:
        keyboard.append(current_row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    logger.info(f"Created audio speed selection keyboard with {len(audio_speeds)} buttons")

    # First answer the callback query
    await query.answer()

    # Then edit message to show audio speed selection
    try:
        await query.edit_message_text(
            text="Select your preferred voice speed:",
            reply_markup=reply_markup
        )
        logger.info(f"Successfully edited message to show audio speed selection for user {user.id}")
    except Exception as e:
        logger.error(f"Error editing message: {e}", exc_info=True)

async def audio_speed_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the audio speed selection callback."""
    query = update.callback_query
    user = update.effective_user
    logger.info(f"AUDIO SPEED SELECT CALLBACK ENTERED for user {user.id} with data: {query.data}")

    audio_speed_id = int(query.data.replace(AUDIO_SPEED_SELECT_PREFIX, ""))
    logger.info(f"Parsed audio_speed_id: {audio_speed_id}")

    # First answer the callback query
    await query.answer()

    # Update user's audio speed preference
    success = update_user_audio_speed(user.id, audio_speed_id)

    if success:
        # Get the selected audio speed
        db_user = get_user_by_telegram_id(user.id)

        # Get audio speed from user_settings
        if hasattr(db_user, 'settings') and db_user.settings and db_user.settings.audio_speed:
            audio_speed_description = db_user.settings.audio_speed.description
            audio_speed_value = db_user.settings.audio_speed.speed
        else:
            # Default to Normal if no settings or audio speed available
            audio_speed_description = "Normal"
            audio_speed_value = 1.0

        # Add emoji based on speed
        # emoji = "🐢" if audio_speed_value < 1.0 else "🐇" if audio_speed_value > 1.0 else "🐾"

        # Confirmation message
        message = f"You have selected {audio_speed_description} voice speed"

        logger.info(f"User {user.id} selected audio speed: {audio_speed_description}")

        # Edit message to show confirmation
        try:
            await query.edit_message_text(text=message)
            logger.info(f"Successfully updated message with confirmation for user {user.id}")
        except Exception as e:
            logger.error(f"Error editing message: {e}", exc_info=True)
    else:
        logger.error(f"Failed to update audio speed preference for user {user.id}")
        try:
            await query.edit_message_text(text="Failed to update audio speed preference. Please try again.")
        except Exception as e:
            logger.error(f"Error editing message: {e}", exc_info=True)


async def language_level_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the language level menu button callback."""
    query = update.callback_query
    user = update.effective_user
    logger.info(f"LANGUAGE LEVEL MENU CALLBACK ENTERED for user {user.id}")

    # Get all available language levels
    language_levels = get_all_language_levels()
    logger.info(f"Retrieved {len(language_levels)} language levels from database")

    if not language_levels:
        logger.error("No language levels found in database. Make sure migrations have been run.")
        await query.answer(text="No language levels available")
        await query.edit_message_text(
            text="Error: No language levels available. Please contact the administrator."
        )
        return

    # Get the user's current language level setting
    db_user = get_user_by_telegram_id(user.id)
    current_language_level_id = None
    if hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language_level:
        current_language_level_id = db_user.settings.language_level.id
        logger.info(f"User {user.id} current language level ID: {current_language_level_id}")

    # Create keyboard with language level buttons (2 buttons per row)
    keyboard = []
    current_row = []

    for language_level in language_levels:
        # Add green checkmark to the current level
        if current_language_level_id and language_level.id == current_language_level_id:
            button_text = f"{language_level.level} ✅"
        else:
            button_text = f"{language_level.level}"

        callback_data = f"{LANGUAGE_LEVEL_SELECT_PREFIX}{language_level.id}"
        logger.info(f"Adding language level button: {button_text} with callback_data: {callback_data}")

        # Add button to current row
        current_row.append(InlineKeyboardButton(
            button_text,
            callback_data=callback_data
        ))

        # If we have 2 buttons in the current row, add it to the keyboard and start a new row
        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []

    # Add any remaining buttons (in case of odd number of buttons)
    if current_row:
        keyboard.append(current_row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    logger.info(f"Created language level selection keyboard with {len(language_levels)} buttons")

    # First answer the callback query
    await query.answer()

    # Then edit message to show language level selection
    try:
        await query.edit_message_text(
            text="Select your preferred language level:",
            reply_markup=reply_markup
        )
        logger.info(f"Successfully edited message to show language level selection for user {user.id}")
    except Exception as e:
        logger.error(f"Error editing message: {e}", exc_info=True)


async def language_level_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the language level selection callback."""
    query = update.callback_query
    user = update.effective_user
    logger.info(f"LANGUAGE LEVEL SELECT CALLBACK ENTERED for user {user.id} with data: {query.data}")

    language_level_id = int(query.data.replace(LANGUAGE_LEVEL_SELECT_PREFIX, ""))
    logger.info(f"Parsed language_level_id: {language_level_id}")

    # First answer the callback query
    await query.answer()

    # Update user's language level preference
    success = update_user_language_level(user.id, language_level_id)

    if success:
        # Get the selected language level
        db_user = get_user_by_telegram_id(user.id)

        # Get language level from user_settings
        if hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language_level:
            language_level = db_user.settings.language_level.level
        else:
            # Default to A2 if no settings or language level available
            language_level = "A2"

        # Confirmation message
        message = f"You have selected language level {language_level}"

        logger.info(f"User {user.id} selected language level: {language_level}")

        # Edit message to show confirmation
        try:
            await query.edit_message_text(text=message)
            logger.info(f"Successfully updated message with confirmation for user {user.id}")
        except Exception as e:
            logger.error(f"Error editing message: {e}", exc_info=True)
    else:
        logger.error(f"Failed to update language level preference for user {user.id}")
        try:
            await query.edit_message_text(text="Failed to update language level preference. Please try again.")
        except Exception as e:
            logger.error(f"Error editing message: {e}", exc_info=True)

async def settings_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings callback queries."""
    query = update.callback_query
    callback_data = query.data
    user = update.effective_user

    logger.info(f"SETTINGS CALLBACK RECEIVED: {callback_data} from user {user.id}")

    # Route to appropriate handler based on callback data
    if callback_data == LANGUAGE_MENU:
        logger.info(f"Routing to language_menu_callback for user {user.id}")
        await language_menu_callback(update, context)
    elif callback_data.startswith(LANGUAGE_SELECT_PREFIX):
        logger.info(f"Routing to language_select_callback for user {user.id}")
        await language_select_callback(update, context)
    elif callback_data == LANGUAGE_LEVEL_MENU:
        logger.info(f"Routing to language_level_menu_callback for user {user.id}")
        await language_level_menu_callback(update, context)
    elif callback_data.startswith(LANGUAGE_LEVEL_SELECT_PREFIX):
        logger.info(f"Routing to language_level_select_callback for user {user.id}")
        await language_level_select_callback(update, context)
    elif callback_data == AUDIO_SPEED_MENU:
        logger.info(f"Routing to audio_speed_menu_callback for user {user.id}")
        await audio_speed_menu_callback(update, context)
    elif callback_data.startswith(AUDIO_SPEED_SELECT_PREFIX):
        logger.info(f"Routing to audio_speed_select_callback for user {user.id}")
        await audio_speed_select_callback(update, context)
    else:
        # Handle unknown callback data
        logger.warning(f"Unknown callback_data received: {callback_data}")
        await query.answer(text="Unknown button")
        await query.edit_message_text(text=f"Unknown action: {callback_data}")
