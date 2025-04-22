"""
Telegram bot implementation module.
"""
import logging
import os
import asyncio
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

def create_spinner():
    spinner_frames = [
        "░░░░░░", "▒░░░░░", "▒▒░░░░", "▒▒▒░░░", "▒▒▒▒░░", "▒▒▒▒▒░",
        "▒▒▒▒▒▒", "▓▒▒▒▒▒", "▓▓▒▒▒▒", "▓▓▓▒▒▒", "▓▓▓▓▒▒", "▓▓▓▓▓▒",
        "▓▓▓▓▓▓", "█▓▓▓▓▓", "██▓▓▓▓", "███▓▓▓", "████▓▓", "█████▓",
        "██████",
    ]

    current_steps = []
    current_progress = spinner_frames[0]
    update_event = asyncio.Event()

    async def task_loop(msg, stop_event):
        i = 0
        while not stop_event.is_set():
            current_progress = spinner_frames[i % len(spinner_frames)]
            full_text = "```\n" + "\n".join(current_steps + [f"> This may take a moment... {current_progress}"]) + "\n```"
            await msg.edit_text(full_text, parse_mode=ParseMode.MARKDOWN_V2)
            i += 1
            try:
                await asyncio.wait_for(update_event.wait(), timeout=0.25)
                update_event.clear()
            except asyncio.TimeoutError:
                pass

        # Финальный чек
        full_text = "```\n" + "\n".join(current_steps + [f"> Done! ✅"]) + "\n```"
        await msg.edit_text(full_text, parse_mode=ParseMode.MARKDOWN_V2)

    def step_done(text: str):
        current_steps.append(f"> {text}")
        update_event.set()

    return task_loop, step_done


async def section_01_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} requested section_01 (Icelandic language test)")

    msg = await update.message.reply_text("```\n> Starting...\n```", parse_mode=ParseMode.MARKDOWN_V2)

    stop_event = asyncio.Event()
    spinner_task_func, step_done = create_spinner()
    spinner = asyncio.create_task(spinner_task_func(msg, stop_event))

    try:
        openai_service = OpenAIService()

        step_done("Generating content...")
        test_content = await asyncio.to_thread(openai_service.generate_icelandic_test)

        step_done("Extracting dialogue from content...")
        dialogue_lines = await asyncio.to_thread(openai_service.extract_dialogue, test_content)

        step_done("Starting audio generation...")
        audio_path = await asyncio.to_thread(openai_service.generate_audio_for_dialogue, dialogue_lines)

        step_done("Merging individual audio files...")
        await asyncio.sleep(0.2)  # визуально задержать

        stop_event.set()
        await spinner

        await update.message.reply_text(test_content, parse_mode=ParseMode.MARKDOWN)

        with open(audio_path, "rb") as audio_file:
            await update.message.reply_audio(audio_file, title="Icelandic Dialogue")

        audio_path_obj = Path(audio_path)
        if audio_path_obj.exists():
            os.remove(audio_path)

        logger.info(f"Successfully sent test and audio to user {user.id}")

    except Exception as e:
        stop_event.set()
        await spinner
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
