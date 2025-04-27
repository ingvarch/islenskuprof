import logging
from telegram import Update
from telegram.constants import ParseMode

from telegram.ext import (
    ContextTypes
)
from bot.utils.access_control import restricted
from bot.utils.user_tracking import track_user_activity
from bot.utils.message_cleaner import delete_user_command_message
from bot.db.user_service import get_user_by_telegram_id

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
    if db_user and hasattr(db_user, 'settings') and db_user.settings:
        if db_user.settings.language:
            language = db_user.settings.language.language
        if db_user.settings.language_level:
            language_level = db_user.settings.language_level.level
        if db_user.settings.audio_speed:
            voice_speed = db_user.settings.audio_speed.description

    # Format welcome message with user settings
    welcome_message = (
        f"Hi, {user.first_name}! Welcome to the bot.\n\n"
        f"*Your settings*:\n"
        f"_Bot Language_: {language}\n"
        f"_Learning level_: {language_level}\n"
        f"_Voice speed_: {voice_speed}"
    )

    await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)

    # Show available commands (previously in help_command)
    help_text = (
        "Available commands :\n"
        "/start - Start interaction with the bot\n"
        "/understanding - Understanding Section (Listening and Reading)\n"
        "/communication - Communication Section\n"
        "/settings - Bot settings\n"
    )
    await update.message.reply_text(help_text, parse_mode=None)

    # Delete the user's command message
    await delete_user_command_message(update, context)

@restricted
@track_user_activity
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with available commands when the command /help is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} requested help")
    help_text = (
        "Available commands :\n"
        "/start - Start interaction with the bot\n"
        "/help - Show list of available commands\n"
        "/understanding - Understanding Section (Listening and Reading)\n"
        "/communication - Communication Section\n"
        "/settings - Bot settings\n"
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
    await update.message.reply_text(
        "Sorry I don't know that command. Type /start to see the list of available commands.",
        parse_mode=ParseMode.MARKDOWN
    )

    # Delete the user's command message
    await delete_user_command_message(update, context)
