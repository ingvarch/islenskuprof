import logging
import os
import asyncio
import random
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from telegram.constants import ParseMode
from bot.utils.spinner import create_spinner
from bot.openai_service import OpenAIService
from bot.utils.access_control import restricted
from bot.utils.user_tracking import track_user_activity
from bot.utils.message_cleaner import delete_user_command_message
from bot.db.person_generator import get_random_person_data
from bot.db.topic_generator import get_random_topic
from bot.db.user_service import get_user_by_telegram_id

# Get logger for this module
logger = logging.getLogger(__name__)

@restricted
@track_user_activity
async def dialogue_story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} requested section_01 (Icelandic language test)")

    msg = await update.message.reply_text("```\nStarting...\n```", parse_mode=ParseMode.MARKDOWN_V2)

    stop_event = asyncio.Event()
    spinner_task_func, start_step, complete_step = create_spinner()
    spinner = asyncio.create_task(spinner_task_func(msg, stop_event))

    try:
        openai_service = OpenAIService()

        # Get user's language preference
        db_user = get_user_by_telegram_id(user.id)
        user_language = "English"  # Default to English if no language preference is set
        if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
            user_language = db_user.settings.language.language
        # No fallback needed anymore as language is only in settings

        # Get a random topic from the database
        start_step("Fetching random topic...")
        topic = get_random_topic()

        if not topic:
            logger.error("Failed to fetch random topic, using default")
            topic = "grocery shopping"

        complete_step()

        custom_prompt = f"""
            Create an Icelandic language proficiency test for citizenship purposes focusing on just ONE dialogue scenario.
            IMPORTANT: The topic for this dialogue is: {topic}

            Listening Section:
            * Create a realistic dialogue between two people (a man and a woman) about the chosen everyday topic.
            * The dialogue should include 8-10 exchanges and be in Icelandic.
            * Include common phrases that would be useful in such a setting.
            * Clearly identify speakers with labels like "Kona:" (Woman) and "Maður:" (Man)
            * After the dialogue, add 3 multiple-choice questions about details in the conversation.
            * Make sure all sections reflect common vocabulary and sentence structures suitable for A2 level in the CEFR framework.
            Format the dialogue clearly so I can easily extract it for audio processing.

            Your output MUST strictly follow this exact template format:


            *Saga:* [title of the dialogue]

            *Hlustaðu á þetta samtal.*

            ```
            [dialogue with speakers clearly identified as "Kona:" and "Maður:"]
            ```

            *Spurningar um samtal*

            [3 multiple-choice questions about the dialogue in Icelandic]

            *Orðabók*

            ```
            Here is the top-20 hardest word or phrases from the text with translation to {user_language}
            * [word] - [translation]
            ```
            """

        start_step(f"Generating content about {topic}...")
        content = await asyncio.to_thread(openai_service.generate_icelandic_test, custom_prompt)
        complete_step()

        start_step("Extracting dialogue from content...")
        dialogue_lines = await asyncio.to_thread(openai_service.extract_dialogue, content)
        complete_step()

        start_step("Starting audio generation...")
        audio_path = await asyncio.to_thread(openai_service.generate_audio_for_dialogue, dialogue_lines, user.id)
        complete_step()

        start_step("Merging individual audio files...")
        await asyncio.sleep(0.2)  # visual delay
        complete_step()

        stop_event.set()
        await spinner

        await update.message.reply_text(content, parse_mode=ParseMode.MARKDOWN)

        with open(audio_path, "rb") as audio_file:
            await update.message.reply_audio(audio_file, title="Icelandic Dialogue")

        audio_path_obj = Path(audio_path)
        if audio_path_obj.exists():
            os.remove(audio_path)

        logger.info(f"Successfully sent test and audio to user {user.id}")

        # Delete the user's command message
        await delete_user_command_message(update, context)

    except Exception as e:
        stop_event.set()
        await spinner
        logger.error(f"Error in section_01 command for user {user.id}: {e}", exc_info=True)
        await update.message.reply_text(f"Sorry, an error occurred: {str(e)}", parse_mode=ParseMode.MARKDOWN)

        # Delete the user's command message even if an error occurred
        await delete_user_command_message(update, context)

@restricted
@track_user_activity
async def about_story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} requested section_02 (Reading Section)")

    msg = await update.message.reply_text("```\nStarting...\n```", parse_mode=ParseMode.MARKDOWN_V2)

    stop_event = asyncio.Event()
    spinner_task_func, start_step, complete_step = create_spinner()
    spinner = asyncio.create_task(spinner_task_func(msg, stop_event))

    try:
        openai_service = OpenAIService()

        # Get user's language preference
        db_user = get_user_by_telegram_id(user.id)
        user_language = "English"  # Default to English if no language preference is set
        if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
            user_language = db_user.settings.language.language
        # No fallback needed anymore as language is only in settings

        start_step("Fetching random person data...")
        person_data = get_random_person_data()

        if not person_data:
            logger.error("Failed to fetch random person data")
            raise Exception("Failed to fetch random person data")

        complete_step()

        # Format the prompt with the person data
        custom_prompt = f"""
        Write a short Icelandic reading comprehension passage - 20-25 sentences long (A2 CEFR level) 
        about a person's daily life in Iceland. 

        Use the following information to guide the story:

        - Name: {person_data["name"]}
        - Gender: {person_data["gender"]}
        - Age: {person_data["age"]}
        - From: {person_data["origin"]}
        - Job: {person_data["job_title"]} at a {person_data["job_workplace"]}
        - Children: {person_data["number_of_children"]} children (ages {person_data["age_of_children"]})
        - Usual weekend activity: {person_data["weekend_activity"]}
        - Plan for today: {person_data["current_plan"]}

        Use simple vocabulary and short sentences. 

        After the passage, add 5 multiple-choice comprehension questions in Icelandic with three answer choices each. 
        The questions should test understanding of where the person is from, what job they do, what time they wake up, 
        etc.

        Your output MUST strictly follow this exact template format:


        *Saga um [person]*

        ```
        [passage"]
        ```

        *Spurningar*

        [5 multiple-choice questions about the passage in Icelandic]

        *Orðabók*

        ```
        Here is the top-20 hardest word or phrases from the text with translation to {user_language}
        * [word] - [translation]
        ```
        """

        start_step(f"Generating content about {person_data['name']}")
        content = await asyncio.to_thread(openai_service.generate_icelandic_test, custom_prompt)

        complete_step()

        stop_event.set()
        await spinner

        await update.message.reply_text(content, parse_mode=ParseMode.MARKDOWN)

        logger.info(f"Successfully sent reading comprehension to user {user.id}")

        # Delete the user's command message
        await delete_user_command_message(update, context)

    except Exception as e:
        stop_event.set()
        await spinner
        logger.error(f"Error in section_02 command for user {user.id}: {e}", exc_info=True)
        await update.message.reply_text(f"Sorry, an error occurred: {str(e)}", parse_mode=ParseMode.MARKDOWN)

        # Delete the user's command message even if an error occurred
        await delete_user_command_message(update, context)

@restricted
@track_user_activity
async def understanding_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /understanding command by randomly selecting between listening and reading sections."""
    user = update.effective_user
    logger.info(f"User {user.id} requested understanding command")

    # Randomly select between dialogue_story and about_story
    if random.choice([True, False]):
        logger.info(f"Randomly selected listening section for user {user.id}")
        await dialogue_story(update, context)
    else:
        logger.info(f"Randomly selected reading section for user {user.id}")
        await about_story(update, context)

@restricted
@track_user_activity
async def communication_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} requested communication command")

    msg = await update.message.reply_text("```\nStarting...\n```", parse_mode=ParseMode.MARKDOWN_V2)

    stop_event = asyncio.Event()
    spinner_task_func, start_step, complete_step = create_spinner()
    spinner = asyncio.create_task(spinner_task_func(msg, stop_event))

    try:
        from bot.db.communication_generator import get_random_communication

        start_step("Fetching communication data...")
        communication_data = get_random_communication()

        if not communication_data:
            logger.error("Failed to fetch communication data")
            raise Exception("Failed to fetch communication data")

        complete_step()

        description = communication_data["description"]
        image_url = communication_data["image_url"]

        stop_event.set()
        await spinner

        await update.message.reply_text(description, parse_mode=ParseMode.MARKDOWN)

        # Check if the image_url is a local path or a URL
        if image_url.startswith(('http://', 'https://')):
            # It's a URL, send it directly
            await update.message.reply_photo(image_url, caption="Write a short paragraph in Icelandic describing this image.")
        else:
            # It's a local path, open the file and send it
            with open(image_url, "rb") as image_file:
                await update.message.reply_photo(image_file, caption="Write a short paragraph in Icelandic describing this image.")

        logger.info(f"Successfully sent communication data to user {user.id}")

        # Delete the user's command message
        await delete_user_command_message(update, context)

    except Exception as e:
        stop_event.set()
        await spinner
        logger.error(f"Error in communication command for user {user.id}: {e}", exc_info=True)
        await update.message.reply_text(f"Sorry, an error occurred: {str(e)}", parse_mode=ParseMode.MARKDOWN)

        # Delete the user's command message even if an error occurred
        await delete_user_command_message(update, context)
