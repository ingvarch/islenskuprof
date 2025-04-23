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

        custom_prompt = """
            Write a short Icelandic reading comprehension passage (A2 CEFR level) about a person’s 
            daily life in Iceland. Include basic personal information (e.g., name, origin, family, age of children), 
            their job, daily routine, weekend activities, and plans for the current day. 
            Use simple vocabulary and short sentences. 
            
            After the passage, add 4–5 multiple-choice comprehension questions in Icelandic with three answer 
            choices each. The questions should check understanding of key facts from the passage such as where 
            the person is from, what job they do, what time they wake up, etc."
            """

        start_step("Generating content...")
        content = await asyncio.to_thread(openai_service.generate_icelandic_test, custom_prompt)

        complete_step()

        stop_event.set()
        await spinner

        await update.message.reply_text(content, parse_mode=ParseMode.MARKDOWN)


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

        custom_prompt = """
        Write a prompt that generates a description of a potential illustration in Icelandic. 
        The description should be 5-7 sentences long and depict a colorful, 
        cartoon-style scene from daily life with multiple diverse characters. 
        The scene should be set in a public place like a café, park, or street, 
        showing people engaged in various everyday activities. 
        Make sure the description captures a lively atmosphere with bright colors and playful details. 
        The final output should ONLY be the 5-7 sentence description in Icelandic, nothing else. 
        """

        start_step("Generating image description...")
        content = await asyncio.to_thread(openai_service.generate_icelandic_test, custom_prompt)

        complete_step()

        start_step("Generating image...")
        image_prompt = content
        image_path = await asyncio.to_thread(openai_service.generate_image, image_prompt)
        complete_step()

        stop_event.set()
        await spinner

        await update.message.reply_text(content, parse_mode=ParseMode.MARKDOWN)

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
    logger.info(f"User {user.id} requested section_04 (Speaking Section)")
    await update.message.reply_text("Speaking Section! Working in progress...")
