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
from bot.utils.translations import get_translation, get_flag_emoji
from bot.db.user_service import (
    get_user_by_telegram_id, update_user_language, get_all_languages,
    get_all_audio_speeds, update_user_audio_speed,
    get_all_language_levels, update_user_language_level,
    get_all_target_languages, get_target_language_by_id, update_user_target_language
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

# Target language callback data prefixes
TARGET_LANGUAGE_PREFIX = "target_lang_"
TARGET_LANGUAGE_MENU = "target_lang_menu"
TARGET_LANGUAGE_SELECT_PREFIX = "target_lang_select_"

@restricted
@track_user_activity
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send settings menu when the command /settings is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} requested settings menu")

    # Get user's language preference
    db_user = get_user_by_telegram_id(user.id)
    language = "English"  # Default to English if no language preference is set
    if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
        language = db_user.settings.language.language

    # Create keyboard with language, target language, language level, and voice speed buttons (2 buttons per row)
    keyboard = [
        [InlineKeyboardButton("🌍 " + get_translation("bot_language", language), callback_data=LANGUAGE_MENU),
         InlineKeyboardButton("📚 " + get_translation("target_language", language), callback_data=TARGET_LANGUAGE_MENU)],
        [InlineKeyboardButton("📝 " + get_translation("learning_level", language), callback_data=LANGUAGE_LEVEL_MENU),
         InlineKeyboardButton("🎧 " + get_translation("voice_speed", language), callback_data=AUDIO_SPEED_MENU)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    logger.info(f"Creating settings keyboard with language, target language, language level, and voice speed buttons")

    # Send message with inline keyboard
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"*{get_translation('settings', language)}*",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"Settings menu sent to user {user.id}")

    # Delete the user's command message
    await delete_user_command_message(update, context)

async def language_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the language menu button callback."""
    query = update.callback_query
    user = update.effective_user
    logger.info(f"LANGUAGE MENU CALLBACK ENTERED for user {user.id}")

    # Get user's current language preference
    db_user = get_user_by_telegram_id(user.id)
    user_language = "English"  # Default to English if no language preference is set
    if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
        user_language = db_user.settings.language.language

    # Get all available languages
    languages = get_all_languages()
    logger.info(f"Retrieved {len(languages)} languages from database")

    if not languages:
        logger.error("No languages found in database. Make sure migrations have been run.")
        await query.answer(text=get_translation("no_languages", user_language))
        await query.edit_message_text(
            text=get_translation("error_no_languages", user_language)
        )
        return

    # Create keyboard with language buttons
    keyboard = []
    for language in languages:
        # Get flag emoji based on language code
        flag = get_flag_emoji(language.code)
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
            text=get_translation("select_language", user_language),
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

        # Get flag emoji based on language code
        flag = get_flag_emoji(language_code)

        # Get confirmation message in the user's newly selected language
        message = get_translation('language_updated', language_name) + f" {flag} ✅"

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
            # Use English as fallback for error message
            await query.edit_message_text(text=get_translation('error_occurred', "English", error="Failed to update language preference"))
        except Exception as e:
            logger.error(f"Error editing message: {e}", exc_info=True)

async def audio_speed_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the audio speed menu button callback."""
    query = update.callback_query
    user = update.effective_user
    logger.info(f"AUDIO SPEED MENU CALLBACK ENTERED for user {user.id}")

    # Get user's language preference
    db_user = get_user_by_telegram_id(user.id)
    language = "English"  # Default to English if no language preference is set
    if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
        language = db_user.settings.language.language

    # Get all available audio speeds
    audio_speeds = get_all_audio_speeds()
    logger.info(f"Retrieved {len(audio_speeds)} audio speeds from database")

    if not audio_speeds:
        logger.error("No audio speeds found in database. Make sure migrations have been run.")
        await query.answer(text=get_translation("no_languages", language))
        await query.edit_message_text(
            text=get_translation("error_no_languages", language)
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
            text=get_translation("select_audio_speed", language),
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

        # Get user's language preference
        language = "English"  # Default to English if no language preference is set
        if hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
            language = db_user.settings.language.language

        # Confirmation message using translation
        message = get_translation("audio_speed_updated", language, speed=audio_speed_description) + " ✅"

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
            # Use English as fallback for error message
            await query.edit_message_text(text=get_translation('error_occurred', "English", error="Failed to update audio speed preference"))
        except Exception as e:
            logger.error(f"Error editing message: {e}", exc_info=True)


async def language_level_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the language level menu button callback."""
    query = update.callback_query
    user = update.effective_user
    logger.info(f"LANGUAGE LEVEL MENU CALLBACK ENTERED for user {user.id}")

    # Get user's language preference
    db_user = get_user_by_telegram_id(user.id)
    language = "English"  # Default to English if no language preference is set
    if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
        language = db_user.settings.language.language

    # Get all available language levels
    language_levels = get_all_language_levels()
    logger.info(f"Retrieved {len(language_levels)} language levels from database")

    if not language_levels:
        logger.error("No language levels found in database. Make sure migrations have been run.")
        await query.answer(text=get_translation("no_languages", language))
        await query.edit_message_text(
            text=get_translation("error_no_languages", language)
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
            text=get_translation("select_language_level", language),
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

        # Get user's language preference
        language = "English"  # Default to English if no language preference is set
        if hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
            language = db_user.settings.language.language

        # Confirmation message using translation
        message = get_translation("language_level_updated", language, level=language_level) + " ✅"

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
            # Use English as fallback for error message
            await query.edit_message_text(text=get_translation('error_occurred', "English", error="Failed to update language level preference"))
        except Exception as e:
            logger.error(f"Error editing message: {e}", exc_info=True)

async def target_language_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the target language menu button callback."""
    query = update.callback_query
    user = update.effective_user
    logger.info(f"TARGET LANGUAGE MENU CALLBACK ENTERED for user {user.id}")

    # Get user's language preference
    db_user = get_user_by_telegram_id(user.id)
    language = "English"  # Default to English if no language preference is set
    if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
        language = db_user.settings.language.language

    # Get all available target languages
    target_languages = get_all_target_languages()
    logger.info(f"Retrieved {len(target_languages)} target languages from database")

    if not target_languages:
        logger.error("No target languages found in database. Make sure migrations have been run and data seeded.")
        await query.answer(text=get_translation("no_languages", language))
        await query.edit_message_text(
            text=get_translation("error_no_target_languages", language)
        )
        return

    # Get the user's current target language setting (use FK column, not lazy-loaded relationship)
    current_target_language_id = None
    if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.target_language_id:
        current_target_language_id = db_user.settings.target_language_id
        logger.info(f"User {user.id} current target language ID: {current_target_language_id}")

    # Create keyboard with target language buttons
    keyboard = []
    for target_lang in target_languages:
        # Add green checkmark to the current target language
        if current_target_language_id and target_lang.id == current_target_language_id:
            button_text = f"{target_lang.native_name} ({target_lang.name}) ✅"
        else:
            button_text = f"{target_lang.native_name} ({target_lang.name})"

        callback_data = f"{TARGET_LANGUAGE_SELECT_PREFIX}{target_lang.id}"
        logger.info(f"Adding target language button: {button_text} with callback_data: {callback_data}")
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=callback_data
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)
    logger.info(f"Created target language selection keyboard with {len(target_languages)} buttons")

    # First answer the callback query
    await query.answer()

    # Then edit message to show target language selection
    try:
        await query.edit_message_text(
            text=get_translation("select_target_language", language),
            reply_markup=reply_markup
        )
        logger.info(f"Successfully edited message to show target language selection for user {user.id}")
    except Exception as e:
        logger.error(f"Error editing message: {e}", exc_info=True)


async def target_language_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the target language selection callback."""
    query = update.callback_query
    user = update.effective_user
    logger.info(f"TARGET LANGUAGE SELECT CALLBACK ENTERED for user {user.id} with data: {query.data}")

    target_language_id = int(query.data.replace(TARGET_LANGUAGE_SELECT_PREFIX, ""))
    logger.info(f"Parsed target_language_id: {target_language_id}")

    # First answer the callback query
    await query.answer()

    # Update user's target language preference
    success = update_user_target_language(user.id, target_language_id)

    if success:
        # Get the selected target language directly by ID (avoid lazy loading issues)
        target_lang = get_target_language_by_id(target_language_id)
        target_lang_name = target_lang.name if target_lang else "Unknown"
        target_lang_native = target_lang.native_name if target_lang else "Unknown"

        # Get user's UI language preference
        db_user = get_user_by_telegram_id(user.id)
        language = "English"  # Default to English if no language preference is set
        if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
            language = db_user.settings.language.language

        # Confirmation message using translation
        message = get_translation("target_language_updated", language, language=f"{target_lang_native} ({target_lang_name})") + " ✅"

        logger.info(f"User {user.id} selected target language: {target_lang_name}")

        # Edit message to show confirmation
        try:
            await query.edit_message_text(text=message)
            logger.info(f"Successfully updated message with confirmation for user {user.id}")
        except Exception as e:
            logger.error(f"Error editing message: {e}", exc_info=True)
    else:
        logger.error(f"Failed to update target language preference for user {user.id}")
        try:
            # Use English as fallback for error message
            await query.edit_message_text(text=get_translation('error_occurred', "English", error="Failed to update target language preference"))
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
    elif callback_data == TARGET_LANGUAGE_MENU:
        logger.info(f"Routing to target_language_menu_callback for user {user.id}")
        await target_language_menu_callback(update, context)
    elif callback_data.startswith(TARGET_LANGUAGE_SELECT_PREFIX):
        logger.info(f"Routing to target_language_select_callback for user {user.id}")
        await target_language_select_callback(update, context)
    else:
        # Handle unknown callback data
        logger.warning(f"Unknown callback_data received: {callback_data}")

        # Get user's language preference
        db_user = get_user_by_telegram_id(user.id)
        language = "English"  # Default to English if no language preference is set
        if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
            language = db_user.settings.language.language

        await query.answer(text=get_translation("unknown_command", language))
        await query.edit_message_text(text=get_translation("error_occurred", language, error=f"Unknown action: {callback_data}"))
