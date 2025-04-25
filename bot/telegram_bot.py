"""
Telegram bot implementation module.
"""
import logging

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from bot.utils.commands import register_bot_commands
from bot.handlers.basic_handlers import (
    start_command,
    help_command,
    unknown_command
)
from bot.handlers.section_handlers import (
    understanding_command,
    communication_command
)
from bot.handlers.settings_handlers import (
    settings_command,
    settings_callback_handler
)

# Get logger for this module
logger = logging.getLogger(__name__)

def create_bot(token: str) -> Application:
    """
    Create and configure the Telegram bot.

    Args:
        token: Telegram bot token from BotFather

    Returns:
        Configured Application instance
    """
    # Create the Application
    logger.info("Creating Telegram bot application")
    application = Application.builder().token(token).build()

    # Add command handlers
    logger.debug("Adding command handlers")
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("understanding", understanding_command))
    application.add_handler(CommandHandler("communication", communication_command))
    application.add_handler(CommandHandler("settings", settings_command))

    # Add callback query handler for settings with explicit pattern
    # This will only handle callback queries that start with 'lang_'
    application.add_handler(CallbackQueryHandler(settings_callback_handler, pattern="lang_*"))

    # Also add a handler for exact match 'lang_menu'
    application.add_handler(CallbackQueryHandler(settings_callback_handler, pattern="^lang_menu$"))

    # Add a generic callback handler for any other patterns
    application.add_handler(CallbackQueryHandler(settings_callback_handler))

    # Add handler for unknown commands - should be added last
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Register commands with Telegram
    application.post_init = register_bot_commands

    logger.info("Bot has been configured and is ready to start")

    return application
