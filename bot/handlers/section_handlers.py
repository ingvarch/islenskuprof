import logging
import os
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from telegram.constants import ParseMode
from bot.utils.spinner import create_spinner
from bot.openai_service import OpenAIService

# Get logger for this module
logger = logging.getLogger(__name__)

async def section_01_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} requested section_01 (Icelandic language test)")

    msg = await update.message.reply_text("```\nStarting...\n```", parse_mode=ParseMode.MARKDOWN_V2)

    stop_event = asyncio.Event()
    spinner_task_func, start_step, complete_step = create_spinner()
    spinner = asyncio.create_task(spinner_task_func(msg, stop_event))

    try:
        openai_service = OpenAIService()

        start_step("Generating content...")
        test_content = await asyncio.to_thread(openai_service.generate_icelandic_test)
        complete_step()

        start_step("Extracting dialogue from content...")
        dialogue_lines = await asyncio.to_thread(openai_service.extract_dialogue, test_content)
        complete_step()

        start_step("Starting audio generation...")
        audio_path = await asyncio.to_thread(openai_service.generate_audio_for_dialogue, dialogue_lines)
        complete_step()

        start_step("Merging individual audio files...")
        await asyncio.sleep(0.2)  # visual delay
        complete_step()

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

async def section_02_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} requested section_02 (Reading Section)")

    msg = await update.message.reply_text("```\nStarting...\n```", parse_mode=ParseMode.MARKDOWN_V2)

    stop_event = asyncio.Event()
    spinner_task_func, start_step, complete_step = create_spinner()
    spinner = asyncio.create_task(spinner_task_func(msg, stop_event))

    try:
        openai_service = OpenAIService()

        start_step("Generating content...")
        test_content = await asyncio.to_thread(openai_service.generate_icelandic_test)
        complete_step()

        stop_event.set()
        await spinner

        await update.message.reply_text(test_content, parse_mode=ParseMode.MARKDOWN)


        logger.info(f"Successfully sent test and audio to user {user.id}")

    except Exception as e:
        stop_event.set()
        await spinner
        logger.error(f"Error in section_01 command for user {user.id}: {e}", exc_info=True)
        await update.message.reply_text(f"Sorry, an error occurred: {str(e)}", parse_mode=ParseMode.MARKDOWN)

async def section_03_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} requested section_02 (Writing Section)")

    msg = await update.message.reply_text("```\nStarting...\n```", parse_mode=ParseMode.MARKDOWN_V2)

    stop_event = asyncio.Event()
    spinner_task_func, start_step, complete_step = create_spinner()
    spinner = asyncio.create_task(spinner_task_func(msg, stop_event))

    try:
        openai_service = OpenAIService()

        start_step("Generating writing prompt image...")
        image_prompt = "A beautiful Icelandic landscape with mountains and a waterfall"
        image_path = await asyncio.to_thread(openai_service.generate_image, image_prompt)
        complete_step()

        stop_event.set()
        await spinner

        with open(image_path, "rb") as image_file:
            await update.message.reply_photo(image_file, caption="Write a short paragraph in Icelandic describing this image.")

        image_path_obj = Path(image_path)
        if image_path_obj.exists():
            os.remove(image_path)

        logger.info(f"Successfully sent writing prompt image to user {user.id}")

    except Exception as e:
        stop_event.set()
        await spinner
        logger.error(f"Error in section_03 command for user {user.id}: {e}", exc_info=True)
        await update.message.reply_text(f"Sorry, an error occurred: {str(e)}", parse_mode=ParseMode.MARKDOWN)

async def section_04_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} requested section_02 (Speaking Section)")
    await update.message.reply_text("Speaking Section! Working in progress...")
