"""
Telegram bot implementation module.
"""
import logging

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from bot.utils.commands import register_bot_commands
from bot.handlers.basic_handlers import (
    start_command,
    help_command,
    unknown_command
)
from bot.handlers.section_handlers import (
    section_01_command,
    section_02_command,
    section_03_command,
    section_04_command
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
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("section_01", section_01_command))
    application.add_handler(CommandHandler("section_02", section_02_command))
    application.add_handler(CommandHandler("section_03", section_03_command))
    application.add_handler(CommandHandler("section_04", section_04_command))
    
    # Add handler for unknown commands - should be added last
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Register commands with Telegram
    application.post_init = register_bot_commands

    logger.info("Bot has been configured and is ready to start")
    
    return application
