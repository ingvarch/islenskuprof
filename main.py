#!/usr/bin/env python3
"""
Main entry point for the Telegram bot application.
"""
import os
import logging
from pathlib import Path
from bot.telegram_bot import create_bot
from bot.db.database import init_db
from run_migrations import run_migrations
from bot.languages import get_language_config

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
    ]
)

# Reduce logging level for some noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main():
    """Main function to start the bot."""
    lang_config = get_language_config()
    logger.info(f"Starting {lang_config.name} Language Learning Bot")

    # Get the bot token from environment variables
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    ai_provider = os.environ.get("AI_PROVIDER", "OPENAI").upper()

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set")
        return

    # Check for the appropriate API key based on the selected AI provider
    logger.info(f"Using AI provider: {ai_provider}")

    if ai_provider == "OPENAI":
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        openai_model = os.environ.get("OPENAI_MODEL")

        if not openai_api_key:
            logger.error("OPENAI_API_KEY environment variable is not set. Bot will not function correctly.")
            return

        if not openai_model:
            logger.error("OPENAI_MODEL environment variable is not set. Bot will not function correctly.")
            return

        logger.info(f"OpenAI API key found, using model: {openai_model}")
    elif ai_provider == "CLAUDE":
        claude_api_key = os.environ.get("CLAUDE_API_KEY")
        claude_model = os.environ.get("CLAUDE_MODEL", "claude-3-7-sonnet-latest")  # Default model if not specified

        if not claude_api_key:
            logger.error("CLAUDE_API_KEY environment variable is not set. Bot will not function correctly.")
            return
        logger.info(f"Claude API key found, using model: {claude_model}")
    elif ai_provider == "OPENROUTER":
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        openrouter_models = os.environ.get("OPENROUTER_MODELS", "")

        if not openrouter_api_key:
            logger.error("OPENROUTER_API_KEY environment variable is not set. Bot will not function correctly.")
            return

        # Log configured models or defaults
        if openrouter_models:
            models_list = [m.strip() for m in openrouter_models.split(",") if m.strip()]
            logger.info(f"OpenRouter API key found, using models: {models_list}")
        else:
            logger.info("OpenRouter API key found, using default failover models")
    else:
        logger.warning(f"Unknown AI provider: {ai_provider}. Falling back to OpenAI.")
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        openai_model = os.environ.get("OPENAI_MODEL")

        if not openai_api_key:
            logger.error("OPENAI_API_KEY environment variable is not set. Bot will not function correctly.")
            return

        if not openai_model:
            logger.error("OPENAI_MODEL environment variable is not set. Bot will not function correctly.")
            return

        logger.info(f"Falling back to OpenAI, using model: {openai_model}")

    # Check for VoiceMaker API key (required for TTS)
    voicemaker_api_key = os.environ.get("VOICEMAKER_API_KEY")
    if not voicemaker_api_key:
        logger.error("VOICEMAKER_API_KEY environment variable is not set (required for TTS). Bot will not function correctly.")
        return
    logger.info("VoiceMaker API key found (required for TTS)")

    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    logger.info(f"Ensured data directory exists: {data_dir}")

    # Run database migrations
    # try:
    #     logger.info("Running database migrations")
    #     migration_success = run_migrations("upgrade")
    #     if not migration_success:
    #         logger.error("Failed to run database migrations")
    #         return
    #     logger.info("Database migrations completed successfully")
    # except Exception as e:
    #     logger.error(f"Error running database migrations: {e}")
    #     return

    # Initialize the database
    try:
        logger.info("Initializing database")
        init_db()
        logger.info("Database initialized successfully")

        # Seed database with language-specific data if tables are empty
        from bot.db.seeder import seed_database_if_empty
        seed_database_if_empty()

        # Clear and fill persons table
        from bot.db.person_generator import clear_and_fill_persons_table
        clear_and_fill_persons_table()
        logger.info("Persons table cleared and filled with random data")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return

    # Create and start the bot
    logger.info("Creating bot instance")
    bot = create_bot(token)

    logger.info("Starting bot polling")
    bot.run_polling()

    logger.info("Bot has stopped")

if __name__ == "__main__":
    main()
