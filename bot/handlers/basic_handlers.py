import logging
from telegram import Update
from telegram.constants import ParseMode

from telegram.ext import ContextTypes
from bot.utils.access_control import restricted
from bot.utils.user_tracking import track_user_activity
from bot.utils.message_cleaner import delete_user_command_message
from bot.db.user_service import get_user_by_telegram_id
from bot.utils.translations import get_translation

# Get logger for this module
logger = logging.getLogger(__name__)


@track_user_activity
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a greeting message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.first_name}) started the bot")

    # Get user settings from database
    db_user = get_user_by_telegram_id(user.id)

    # Default values in case settings are not available
    language = "English"
    language_level = "A2"
    voice_speed = "Normal"

    # Get actual settings if available
    if db_user and hasattr(db_user, "settings") and db_user.settings:
        if db_user.settings.language:
            language = db_user.settings.language.language
        if db_user.settings.language_level:
            language_level = db_user.settings.language_level.level
        if db_user.settings.audio_speed:
            voice_speed = db_user.settings.audio_speed.description

    # Format welcome message with user settings using translations
    welcome_message = (
        f"{get_translation('welcome', language, first_name=user.first_name)}\n\n"
        f"*{get_translation('your_settings', language)}*:\n"
        f"_{get_translation('bot_language', language)}_: {language}\n"
        f"_{get_translation('learning_level', language)}_: {language_level}\n"
        f"_{get_translation('voice_speed', language)}_: {voice_speed}"
    )

    await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

    # Show available commands with translations
    help_text = (
        f"{get_translation('available_commands', language)} :\n"
        f"/start - {get_translation('cmd_start', language)}\n"
        f"/understanding - {get_translation('cmd_understanding', language)}\n"
        f"/communication - {get_translation('cmd_communication', language)}\n"
        f"/settings - {get_translation('cmd_settings', language)}\n"
    )
    await update.message.reply_text(help_text, parse_mode=None)

    # Delete the user's command message
    await delete_user_command_message(update, context)


@restricted
@track_user_activity
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    user = update.effective_user
    command = update.message.text
    logger.info(f"User {user.id} sent unknown command: {command}")

    # Get user's language preference
    db_user = get_user_by_telegram_id(user.id)
    language = "English"  # Default to English if no language preference is set
    if (
        db_user
        and hasattr(db_user, "settings")
        and db_user.settings
        and db_user.settings.language
    ):
        language = db_user.settings.language.language

    await update.message.reply_text(
        get_translation("unknown_command", language), parse_mode=ParseMode.MARKDOWN
    )

    # Delete the user's command message
    await delete_user_command_message(update, context)
