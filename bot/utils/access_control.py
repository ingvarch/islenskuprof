"""
Access control utilities for the Telegram bot.
"""

import os
import logging
from functools import wraps
from typing import List, Callable
from telegram import Update
from telegram.ext import ContextTypes

# Get logger for this module
logger = logging.getLogger(__name__)


def get_allowed_users() -> List[int]:
    """
    Parse the ALLOWED_USERS environment variable to get a list of allowed Telegram user IDs.

    Returns:
        List of allowed Telegram user IDs as integers.
    """
    allowed_users_str = os.environ.get("ALLOWED_USERS", "")
    if not allowed_users_str:
        logger.warning(
            "ALLOWED_USERS environment variable is not set. No users will be allowed to access the bot."
        )
        return []

    try:
        # Split by comma and convert to integers
        allowed_users = [
            int(user_id.strip())
            for user_id in allowed_users_str.split(",")
            if user_id.strip()
        ]
        logger.info(
            f"Loaded {len(allowed_users)} allowed users from environment variable"
        )
        return allowed_users
    except ValueError as e:
        logger.error(
            f"Error parsing ALLOWED_USERS environment variable: {e}. Format should be comma-separated integers."
        )
        return []


def restricted(func: Callable) -> Callable:
    """
    Decorator to restrict access to the bot to only allowed users.

    Args:
        func: The handler function to wrap.

    Returns:
        Wrapped function that checks if the user is allowed before executing the handler.
    """

    @wraps(func)
    async def wrapped(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user = update.effective_user
        user_id = user.id
        allowed_users = get_allowed_users()

        if not allowed_users or user_id in allowed_users:
            return await func(update, context, *args, **kwargs)
        else:
            logger.warning(f"Access denied for user {user_id} ({user.first_name})")
            await update.message.reply_text(
                "Access Denied. You are not authorized to use this bot."
            )
            return None

    return wrapped
