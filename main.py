#!/usr/bin/env python3
"""
Main entry point for the Telegram bot application.
"""
import os
import logging
from pathlib import Path
from bot.telegram_bot import create_bot

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)

# Reduce logging level for some noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main():
    """Main function to start the bot."""
    logger.info("Starting Icelandic Citizenship Test Bot")
    
    # Get the bot token from environment variables
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set")
        return
    
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable is not set. Bot will not function correctly.")
        return
    
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    logger.info(f"Ensured data directory exists: {data_dir}")
    
    # Create and start the bot
    logger.info("Creating bot instance")
    bot = create_bot(token)
    
    logger.info("Starting bot polling")
    bot.run_polling()
    
    logger.info("Bot has stopped")

if __name__ == "__main__":
    main()
