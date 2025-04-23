"""
User tracking utilities for the Telegram bot.
"""
import logging
import functools
from telegram import Update
from telegram.ext import ContextTypes
from bot.db.user_service import get_or_create_user, update_user_last_contact

# Get logger for this module
logger = logging.getLogger(__name__)

def track_user_activity(func):
    """
    Decorator to track user activity in the database.
    
    This decorator updates the user's last_contact timestamp in the database
    whenever they interact with the bot.
    
    Args:
        func: The handler function to wrap.
        
    Returns:
        Wrapped function that updates user information before executing the handler.
    """
    @functools.wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user:
            try:
                # Get or create user in the database
                get_or_create_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                
                # Update last_contact timestamp
                update_user_last_contact(user.id)
                
                logger.debug(f"Updated last_contact for user {user.id}")
            except Exception as e:
                logger.error(f"Error tracking user activity: {e}")
        
        # Call the original handler
        return await func(update, context, *args, **kwargs)
    
    return wrapped
