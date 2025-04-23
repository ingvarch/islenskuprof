import logging
from telegram import Update
from telegram.constants import ParseMode

from telegram.ext import (
    ContextTypes
)
from bot.utils.access_control import restricted
from bot.utils.user_tracking import track_user_activity

# Get logger for this module
logger = logging.getLogger(__name__)

@restricted
@track_user_activity
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a greeting message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.first_name}) started the bot")
    await update.message.reply_text(f"Hi, {user.first_name}! Welcome to the bot.", parse_mode=ParseMode.MARKDOWN)

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
        "/section_01 - Listening Section\n"
        "/section_02 - Reading Section\n"
        "/section_03 - Writing Section\n"
        "/section_04 - Speaking Section\n"
    )
    await update.message.reply_text(help_text, parse_mode=None)

@restricted
@track_user_activity
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    user = update.effective_user
    command = update.message.text
    logger.info(f"User {user.id} sent unknown command: {command}")
    await update.message.reply_text(
        "Sorry I don't know that command. Type /help to see the list of available commands.",
        parse_mode=ParseMode.MARKDOWN
    )
