"""
Telegram bot implementation module.
"""
import logging
import os
from pathlib import Path
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from bot.openai_service import OpenAIService

# Get logger for this module
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a greeting message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.first_name}) started the bot")
    await update.message.reply_text(f"Hi, {user.first_name}! Welcome to the bot.", parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with available commands when the command /help is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} requested help")
    help_text = (
        "Available commands :\n"
        "/start - Start interaction with the bot\n"
        "/help - Show list of available commands\n"
        "/section_01 - Generate Icelandic language test with audio dialogue\n"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    user = update.effective_user
    command = update.message.text
    logger.info(f"User {user.id} sent unknown command: {command}")
    await update.message.reply_text(
        "Sorry I don't know that command. Type /help to see the list of available commands.",
        parse_mode=ParseMode.MARKDOWN
    )

async def section_01_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send Icelandic language test content with audio."""
    user = update.effective_user
    logger.info(f"User {user.id} requested section_01 (Icelandic language test)")
    await update.message.reply_text("Generating Icelandic language test content. This may take a moment...", 
                                   parse_mode=ParseMode.MARKDOWN)
    
    try:
        # Initialize OpenAI service
        logger.debug("Initializing OpenAI service")
        openai_service = OpenAIService()
        
        # Generate test content
        logger.info("Generating Icelandic test content")
        test_content = openai_service.generate_icelandic_test()
        logger.debug(f"Test content generated ({len(test_content)} characters)")
        
        # Extract dialogue from the content
        logger.info("Extracting dialogue from test content")
        dialogue_lines = openai_service.extract_dialogue(test_content)
        logger.info(f"Extracted {len(dialogue_lines)} dialogue lines")
        
        # Generate audio for the dialogue
        logger.info("Starting audio generation")
        audio_path = openai_service.generate_audio_for_dialogue(dialogue_lines)
        logger.info(f"Audio generated and saved to {audio_path}")
        
        # Send the test content
        logger.debug("Sending test content to user")
        await update.message.reply_text(test_content, parse_mode=ParseMode.MARKDOWN)
        
        # Send the audio file
        audio_path_obj = Path(audio_path)
        logger.debug(f"Sending audio file to user: {audio_path}")
        with open(audio_path, "rb") as audio_file:
            await update.message.reply_audio(audio_file, title="Icelandic Dialogue")
            
        # Delete the audio file after sending
        try:
            if audio_path_obj.exists():
                os.remove(audio_path)
                logger.info(f"Successfully deleted audio file: {audio_path}")
        except Exception as e:
            logger.error(f"Error deleting audio file {audio_path}: {e}")
            
        logger.info(f"Successfully sent test and audio to user {user.id}")
        
    except Exception as e:
        logger.error(f"Error in section_01 command for user {user.id}: {e}", exc_info=True)
        await update.message.reply_text(f"Sorry, an error occurred: {str(e)}", parse_mode=ParseMode.MARKDOWN)

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
    
    # Add handler for unknown commands - should be added last
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    logger.info("Bot has been configured and is ready to start")
    
    return application
