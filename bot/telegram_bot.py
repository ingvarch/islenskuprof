"""
Telegram bot implementation module.
"""

import logging
from typing import Optional

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from bot.utils.commands import register_bot_commands
from bot.handlers.basic_handlers import start_command, unknown_command
from bot.handlers.section_handlers import understanding_command, communication_command
from bot.handlers.settings_handlers import settings_command, settings_callback_handler
from bot.handlers.pimsleur_handlers import (
    pimsleur_command,
    pimsleur_callback_handler,
    handle_pimsleur_text_input,
)

# Get logger for this module
logger = logging.getLogger(__name__)


def create_bot(token: str, redis_url: Optional[str] = None) -> Application:
    """
    Create and configure the Telegram bot.

    Args:
        token: Telegram bot token from BotFather
        redis_url: Optional Redis URL for state persistence

    Returns:
        Configured Application instance
    """
    # Create the Application with optional persistence
    logger.info("Creating Telegram bot application")
    builder = Application.builder().token(token).concurrent_updates(8)

    if redis_url:
        from bot.persistence import RedisPersistence

        persistence = RedisPersistence(redis_url)
        builder = builder.persistence(persistence)

    application = builder.build()

    # Add command handlers
    logger.debug("Adding command handlers")
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("understanding", understanding_command))
    application.add_handler(CommandHandler("communication", communication_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("pimsleur", pimsleur_command))

    # Add callback query handler for Pimsleur (before generic handlers)
    application.add_handler(
        CallbackQueryHandler(pimsleur_callback_handler, pattern="^pimsleur_")
    )

    # Add callback query handler for settings with explicit pattern
    # This will only handle callback queries that start with 'lang_'
    application.add_handler(
        CallbackQueryHandler(settings_callback_handler, pattern="lang_*")
    )

    # Also add a handler for exact match 'lang_menu'
    application.add_handler(
        CallbackQueryHandler(settings_callback_handler, pattern="^lang_menu$")
    )

    # Add a generic callback handler for any other patterns
    application.add_handler(CallbackQueryHandler(settings_callback_handler))

    # Add text handler for Pimsleur custom lesson input (with group for priority)
    async def pimsleur_text_wrapper(update, context):
        """Wrapper to handle Pimsleur text input, pass through if not handled."""
        handled = await handle_pimsleur_text_input(update, context)
        if not handled:
            # Not a Pimsleur text input, let other handlers process it
            pass

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, pimsleur_text_wrapper), group=1
    )

    # Add handler for unknown commands - should be added last
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Register commands with Telegram
    application.post_init = register_bot_commands

    logger.info("Bot has been configured and is ready to start")

    return application
