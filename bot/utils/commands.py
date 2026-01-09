import logging
from telegram import BotCommand
from telegram.ext import Application

logger = logging.getLogger(__name__)

async def register_bot_commands(application: Application) -> None:
    """
    Register bot commands with Telegram to show in the command menu.
    """
    # Define commands with descriptions
    commands = [
        BotCommand("start", "Start interaction with the bot"),
        BotCommand("understanding", "Understanding Section (Listening and Reading)"),
        BotCommand("communication", "Communication Section"),
        BotCommand("pimsleur", "Pimsleur-style audio lessons"),
        BotCommand("settings", "Bot settings")
    ]

    try:
        # Set commands for the bot
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands have been registered with Telegram")
    except Exception as e:
        logger.error(f"Failed to register bot commands: {e}")
