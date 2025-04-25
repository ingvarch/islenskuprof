"""
Settings handlers module for the Telegram bot.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

from bot.utils.access_control import restricted
from bot.utils.user_tracking import track_user_activity
from bot.db.user_service import get_user_by_telegram_id, update_user_language, get_all_languages

# Get logger for this module
logger = logging.getLogger(__name__)

# Callback data prefixes
LANGUAGE_PREFIX = "lang_"
LANGUAGE_MENU = "lang_menu"
LANGUAGE_SELECT_PREFIX = "lang_select_"

@restricted
@track_user_activity
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send settings menu when the command /settings is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} requested settings menu")

    # Create keyboard with language button
    keyboard = [
        [InlineKeyboardButton("Language", callback_data=LANGUAGE_MENU)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    logger.info(f"Creating settings keyboard with language button, callback_data='{LANGUAGE_MENU}'")

    # Send message with inline keyboard
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Settings",
        reply_markup=reply_markup
    )
    logger.info(f"Settings menu sent to user {user.id}")

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
        language_name = db_user.language.language
        language_code = db_user.language.code

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
    else:
        # Handle unknown callback data
        logger.warning(f"Unknown callback_data received: {callback_data}")
        await query.answer(text="Unknown button")
        await query.edit_message_text(text=f"Unknown action: {callback_data}")
