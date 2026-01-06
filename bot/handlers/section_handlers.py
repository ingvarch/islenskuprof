import logging
import os
import asyncio
import random
import re
from pathlib import Path
from telegram import Update, Poll
from telegram.ext import ContextTypes

from telegram.constants import ParseMode
from bot.utils.spinner import create_spinner
from bot.ai_service import get_ai_service
from bot.utils.access_control import restricted
from bot.utils.user_tracking import track_user_activity
from bot.utils.message_cleaner import delete_user_command_message
from bot.utils.translations import get_translation
from bot.db.person_generator import get_random_person_data
from bot.db.topic_generator import get_random_topic
from bot.db.user_service import get_user_by_telegram_id, get_target_language_by_id
from bot.languages import get_language_config, get_language_config_by_code

# Get logger for this module
logger = logging.getLogger(__name__)


def get_user_target_language(db_user):
    """
    Get the user's target language code from their settings.

    Args:
        db_user: User object from database

    Returns:
        str: Language code (e.g., 'is', 'de') or None if not set
    """
    if db_user and db_user.settings and db_user.settings.target_language_id:
        target_lang = get_target_language_by_id(db_user.settings.target_language_id)
        if target_lang:
            return target_lang.code
    return None


def get_lang_config_for_user(db_user):
    """
    Get the language config for a user based on their target language setting.

    Args:
        db_user: User object from database

    Returns:
        LanguageConfig instance for the user's target language
    """
    target_lang_code = get_user_target_language(db_user)
    if target_lang_code:
        config = get_language_config_by_code(target_lang_code)
        if config:
            return config
    # Fall back to default language
    return get_language_config()

# Dictionary to track ongoing requests per user and command type
# Key: (user_id, command_type), Value: True if processing
ongoing_requests = {}

async def parse_and_send_quiz_polls(update: Update, content: str, marker: str) -> None:
    """
    Parse multiple-choice questions from content and send them as quiz polls.

    Args:
        update: The update object from Telegram
        content: The content containing the questions
        marker: The marker that precedes the questions section (e.g., "*Spurningar*")
    """
    # Extract the questions section
    parts = content.split(marker, 1)
    if len(parts) != 2:
        logger.warning("Failed to find questions section")
        return

    # Get the questions part (everything after the marker until the next section marker)
    questions_text = parts[1].strip()
    next_section = questions_text.find("*")
    if next_section != -1:
        questions_text = questions_text[:next_section].strip()

    # Split into individual questions
    # Look for patterns like "1. Question" or "1) Question" or just numbered lines
    questions = re.split(r'\n\s*\d+[\.\)]\s+|\n\s*\d+\.\s+|\n\s*\d+\s+', questions_text)
    questions = [q.strip() for q in questions if q.strip()]

    if not questions:
        logger.warning("No questions found in the content")
        return

    # Process each question
    for question in questions:
        # Split the question into the question text and options
        lines = question.split('\n')
        if not lines:
            continue

        question_text = lines[0].strip()
        options = []
        correct_option_id = 0  # Default to first option if no marker found

        # Extract options (a, b, c) or (A, B, C) format
        for i, line in enumerate(lines[1:]):
            line = line.strip()
            if not line:
                continue

            # Remove option markers like a), b), c) or A), B), C)
            option_match = re.match(r'^[a-zA-Z]\)\s*(.+)$', line)
            if option_match:
                option_text = option_match.group(1).strip()
            else:
                option_text = line

            # Check if this option is marked as correct with (CORRECT) marker
            is_correct = False
            if "(CORRECT)" in option_text:
                is_correct = True
                option_text = option_text.replace("(CORRECT)", "").strip()
                correct_option_id = len(options)  # Current position will be the correct answer

            options.append(option_text)

        if options:
            # Shuffle the options while keeping track of correct answer
            combined = list(zip(options, [i == correct_option_id for i in range(len(options))]))
            random.shuffle(combined)
            options, correct_positions = zip(*combined)
            options = list(options)
            correct_option_id = correct_positions.index(True)

            # Send the poll
            await update.message.reply_poll(
                question=question_text,
                options=options,
                type=Poll.QUIZ,
                correct_option_id=correct_option_id,
                is_anonymous=False
            )

@restricted
@track_user_activity
async def dialogue_story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    # Get user from database
    db_user = get_user_by_telegram_id(user.id)

    # Get language config based on user's target language setting
    lang_config = get_lang_config_for_user(db_user)
    target_lang_code = lang_config.code

    logger.info(f"User {user.id} requested section_01 ({lang_config.name} language test)")

    # Get user's UI language preference
    user_language = "English"  # Default to English if no language preference is set
    if db_user and db_user.settings and db_user.settings.language:
        user_language = db_user.settings.language.language

    msg = await update.message.reply_text(f"```\n{get_translation('starting', user_language)}\n```", parse_mode=ParseMode.MARKDOWN_V2)

    stop_event = asyncio.Event()
    spinner_task_func, start_step, complete_step = create_spinner()
    spinner = asyncio.create_task(spinner_task_func(msg, stop_event))

    try:
        ai_service = get_ai_service()

        # Get user's language level
        user_language_level = "A2"  # Default to A2 if no language level is set
        if db_user and db_user.settings and db_user.settings.language_level:
            user_language_level = db_user.settings.language_level.level

        # Get a random topic from the database for the target language
        start_step(get_translation("fetching_topic", user_language))
        topic = get_random_topic(target_lang_code)

        if not topic:
            logger.error("Failed to fetch random topic, using default")
            topic = "grocery shopping"

        complete_step()

        # Get prompt from language configuration
        custom_prompt = lang_config.get_dialogue_prompt(topic, user_language, user_language_level)

        start_step(get_translation("generating_content", user_language, topic=topic))
        content = await asyncio.to_thread(ai_service.generate_icelandic_test, custom_prompt)
        complete_step()

        start_step(get_translation("extracting_dialogue", user_language))
        dialogue_lines = await asyncio.to_thread(ai_service.extract_dialogue, content, lang_config)
        complete_step()

        start_step(get_translation("starting_audio", user_language))
        audio_path = await asyncio.to_thread(ai_service.generate_audio_for_dialogue, dialogue_lines, user.id, lang_config)
        complete_step()

        start_step(get_translation("merging_audio", user_language))
        await asyncio.sleep(0.2)  # visual delay
        complete_step()

        stop_event.set()
        await spinner

        # Split content into parts
        # 1. Title and dialogue section
        # 2. Audio file (already separate)
        # 3. Questions (to be sent as polls)
        # 4. Dictionary/vocabulary sections

        # Get markers from language config
        dialogue_end_marker = lang_config.markers.dialogue_questions
        vocabulary_marker = lang_config.markers.vocabulary

        # Split the content
        parts = content.split(dialogue_end_marker, 1)

        if len(parts) == 2:
            first_part = parts[0].strip()
            remaining_content = parts[1].strip()

            # Further split to separate questions from vocabulary
            vocab_parts = remaining_content.split(vocabulary_marker, 1)
            if len(vocab_parts) == 2:
                vocabulary_part = vocabulary_marker + vocab_parts[1].strip()
            else:
                vocabulary_part = ""

            # Send first part (title and dialogue)
            await update.message.reply_text(first_part, parse_mode=ParseMode.MARKDOWN)

            # Send audio file
            with open(audio_path, "rb") as audio_file:
                await update.message.reply_audio(audio_file, title=f"{lang_config.name} Dialogue")

            # Send questions as quiz polls
            await parse_and_send_quiz_polls(update, content, dialogue_end_marker)

            # Send vocabulary part if it exists
            if vocabulary_part:
                await update.message.reply_text(vocabulary_part, parse_mode=ParseMode.MARKDOWN)
        else:
            # Fallback if splitting fails
            logger.warning("Failed to split content, sending as a single message")
            await update.message.reply_text(content, parse_mode=ParseMode.MARKDOWN)

            with open(audio_path, "rb") as audio_file:
                await update.message.reply_audio(audio_file, title=f"{lang_config.name} Dialogue")

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
        await update.message.reply_text(get_translation("error_occurred", user_language, error=str(e)), parse_mode=ParseMode.MARKDOWN)

        # Delete the user's command message even if an error occurred
        await delete_user_command_message(update, context)

@restricted
@track_user_activity
async def about_story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    # Get user from database
    db_user = get_user_by_telegram_id(user.id)

    # Get language config based on user's target language setting
    lang_config = get_lang_config_for_user(db_user)
    target_lang_code = lang_config.code

    logger.info(f"User {user.id} requested section_02 ({lang_config.name} Reading Section)")

    # Get user's UI language preference
    user_language = "English"  # Default to English if no language preference is set
    if db_user and db_user.settings and db_user.settings.language:
        user_language = db_user.settings.language.language

    msg = await update.message.reply_text(f"```\n{get_translation('starting', user_language)}\n```", parse_mode=ParseMode.MARKDOWN_V2)

    stop_event = asyncio.Event()
    spinner_task_func, start_step, complete_step = create_spinner()
    spinner = asyncio.create_task(spinner_task_func(msg, stop_event))

    try:
        ai_service = get_ai_service()

        # Get user's language level
        user_language_level = "A2"  # Default to A2 if no language level is set
        if db_user and db_user.settings and db_user.settings.language_level:
            user_language_level = db_user.settings.language_level.level

        start_step(get_translation("fetching_person", user_language))
        person_data = get_random_person_data(target_lang_code)

        if not person_data:
            logger.error("Failed to fetch random person data")
            raise Exception("Failed to fetch random person data")

        complete_step()

        # Format the prompt with the person data
        start_step(get_translation("generating_content", user_language, topic=person_data['name']))

        # Get prompt from language configuration
        custom_prompt = lang_config.get_reading_prompt(person_data, user_language, user_language_level)
        content = await asyncio.to_thread(ai_service.generate_icelandic_test, custom_prompt)
        complete_step()

        stop_event.set()
        await spinner

        # Split content into parts
        # 1. Passage section
        # 2. Questions (to be sent as polls)
        # 3. Dictionary/vocabulary sections

        # Get markers from language config
        questions_marker = lang_config.markers.reading_questions
        vocabulary_marker = lang_config.markers.vocabulary

        # Split to get the passage part
        passage_parts = content.split(questions_marker, 1)

        if len(passage_parts) == 2:
            passage_part = passage_parts[0].strip()
            remaining_content = passage_parts[1].strip()

            # Further split to separate questions from vocabulary
            vocab_parts = remaining_content.split(vocabulary_marker, 1)
            if len(vocab_parts) == 2:
                vocabulary_part = vocabulary_marker + vocab_parts[1].strip()
            else:
                vocabulary_part = ""

            # Send passage part
            await update.message.reply_text(passage_part, parse_mode=ParseMode.MARKDOWN)

            # Send questions as quiz polls
            await parse_and_send_quiz_polls(update, content, questions_marker)

            # Send vocabulary part if it exists
            if vocabulary_part:
                await update.message.reply_text(vocabulary_part, parse_mode=ParseMode.MARKDOWN)
        else:
            # Fallback if splitting fails
            logger.warning("Failed to split content, sending as a single message")
            await update.message.reply_text(content, parse_mode=ParseMode.MARKDOWN)

        logger.info(f"Successfully sent reading comprehension to user {user.id}")

        # Delete the user's command message
        await delete_user_command_message(update, context)

    except Exception as e:
        stop_event.set()
        await spinner
        logger.error(f"Error in section_02 command for user {user.id}: {e}", exc_info=True)
        await update.message.reply_text(get_translation("error_occurred", user_language, error=str(e)), parse_mode=ParseMode.MARKDOWN)

        # Delete the user's command message even if an error occurred
        await delete_user_command_message(update, context)

@restricted
@track_user_activity
async def understanding_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /understanding command by alternating between listening and reading sections for each user."""
    user = update.effective_user
    logger.info(f"User {user.id} requested understanding command")

    # Get user from database
    db_user = get_user_by_telegram_id(user.id)

    # Get user's language preference
    user_language = "English"  # Default to English if no language preference is set
    if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
        user_language = db_user.settings.language.language

    # Check if user already has an ongoing request
    if (user.id, "understanding") in ongoing_requests:
        logger.info(f"User {user.id} already has an ongoing understanding request")
        # Send popup message
        await update.message.reply_text(
            get_translation("already_processing", user_language),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        # Mark user as having an ongoing request
        ongoing_requests[(user.id, "understanding")] = True

        # Determine which section to show based on last selection
        if not db_user or not db_user.settings or not db_user.settings.last_section or db_user.settings.last_section == 'reading':
            # If no previous selection or last was reading, show listening
            logger.info(f"Selected listening section for user {user.id} (alternating)")
            await dialogue_story(update, context)
            # Update the last section
            from bot.db.user_service import update_user_last_section
            update_user_last_section(user.id, 'listening')
        else:
            # If last was listening, show reading
            logger.info(f"Selected reading section for user {user.id} (alternating)")
            await about_story(update, context)
            # Update the last section
            from bot.db.user_service import update_user_last_section
            update_user_last_section(user.id, 'reading')
    finally:
        # Remove user from ongoing requests, even if an error occurred
        if (user.id, "understanding") in ongoing_requests:
            del ongoing_requests[(user.id, "understanding")]
            logger.info(f"Removed user {user.id} from ongoing understanding requests")

@restricted
@track_user_activity
async def communication_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    # Get user from database
    db_user = get_user_by_telegram_id(user.id)

    # Get language config based on user's target language setting
    lang_config = get_lang_config_for_user(db_user)

    logger.info(f"User {user.id} requested communication command ({lang_config.name})")

    # Get user's UI language preference
    user_language = "English"  # Default to English if no language preference is set
    if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
        user_language = db_user.settings.language.language

    # Check if user already has an ongoing request
    if (user.id, "communication") in ongoing_requests:
        logger.info(f"User {user.id} already has an ongoing communication request")
        # Send popup message
        await update.message.reply_text(
            get_translation("already_processing", user_language),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Mark user as having an ongoing request
    ongoing_requests[(user.id, "communication")] = True

    msg = await update.message.reply_text(f"```\n{get_translation('starting', user_language)}\n```", parse_mode=ParseMode.MARKDOWN_V2)

    stop_event = asyncio.Event()
    spinner_task_func, start_step, complete_step = create_spinner()
    spinner = asyncio.create_task(spinner_task_func(msg, stop_event))

    try:
        from bot.db.communication_generator import get_random_communication

        start_step(get_translation("fetching_communication", user_language))
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
        caption = get_translation("write_paragraph", user_language, target_language=lang_config.name)
        if image_url.startswith(('http://', 'https://')):
            # It's a URL, send it directly
            await update.message.reply_photo(image_url, caption=caption)
        else:
            # It's a local path, open the file and send it
            with open(image_url, "rb") as image_file:
                await update.message.reply_photo(image_file, caption=caption)

        logger.info(f"Successfully sent communication data to user {user.id}")

        # Delete the user's command message
        await delete_user_command_message(update, context)

    except Exception as e:
        stop_event.set()
        await spinner
        logger.error(f"Error in communication command for user {user.id}: {e}", exc_info=True)
        await update.message.reply_text(get_translation("error_occurred", user_language, error=str(e)), parse_mode=ParseMode.MARKDOWN)

        # Delete the user's command message even if an error occurred
        await delete_user_command_message(update, context)
    finally:
        # Remove user from ongoing requests, even if an error occurred
        if (user.id, "communication") in ongoing_requests:
            del ongoing_requests[(user.id, "communication")]
            logger.info(f"Removed user {user.id} from ongoing communication requests")
