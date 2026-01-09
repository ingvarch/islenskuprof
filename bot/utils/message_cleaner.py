"""
Utility module for cleaning up messages in the Telegram bot.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

# Get logger for this module
logger = logging.getLogger(__name__)


async def delete_user_command_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Delete the user's command message.

    Args:
        update: The update object containing the message to delete
        context: The context object
    """
    if update.message:
        try:
            await update.message.delete()
            logger.debug(
                f"Deleted command message from user {update.effective_user.id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to delete message from user {update.effective_user.id}: {e}",
                exc_info=True,
            )
