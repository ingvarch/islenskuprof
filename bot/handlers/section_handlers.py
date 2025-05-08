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
from bot.db.user_service import get_user_by_telegram_id

# Get logger for this module
logger = logging.getLogger(__name__)

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
    logger.info(f"User {user.id} requested section_01 (Icelandic language test)")

    # Get user's language preference
    db_user = get_user_by_telegram_id(user.id)
    user_language = "English"  # Default to English if no language preference is set
    if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
        user_language = db_user.settings.language.language

    msg = await update.message.reply_text(f"```\n{get_translation('starting', user_language)}\n```", parse_mode=ParseMode.MARKDOWN_V2)

    stop_event = asyncio.Event()
    spinner_task_func, start_step, complete_step = create_spinner()
    spinner = asyncio.create_task(spinner_task_func(msg, stop_event))

    try:
        ai_service = get_ai_service()

        # Get user's language preference and language level
        db_user = get_user_by_telegram_id(user.id)
        user_language = "English"  # Default to English if no language preference is set
        user_language_level = "A2"  # Default to A2 if no language level is set
        if db_user and hasattr(db_user, 'settings') and db_user.settings:
            if db_user.settings.language:
                user_language = db_user.settings.language.language
            if db_user.settings.language_level:
                user_language_level = db_user.settings.language_level.level
        # No fallback needed anymore as language is only in settings

        # Get a random topic from the database
        start_step(get_translation("fetching_topic", user_language))
        topic = get_random_topic()

        if not topic:
            logger.error("Failed to fetch random topic, using default")
            topic = "grocery shopping"

        complete_step()

        custom_prompt = f"""
            Create an Icelandic language proficiency test for citizenship purposes focusing on just ONE dialogue scenario.
            IMPORTANT: The topic for this dialogue is: {topic}
            
            STRICTLY follow these guidelines for {user_language_level} level according to CEFR:
            * A1: Only use basic phrases, present tense, simple questions. Vocabulary limited to 500 most common words. Only simple sentences (subject-verb-object).
            * A2: Simple past tense allowed, basic conjunctions, vocabulary up to 1000 most common words. Simple sentences with basic connectors.
            * B1: Some compound sentences, more verb tenses, vocabulary up to 2000 most common words. Avoid idioms and complex structures.
            * B2: Natural flow of conversation, wider range of vocabulary up to 4000 words, some idioms allowed but explained in footnotes.
            * C1-C2: No restrictions on vocabulary or grammar complexity.
            
            Listening Section:
            * Create a realistic dialogue between two people (a man and a woman) about the chosen everyday topic.
            * The dialogue should include 8-10 exchanges and be in Icelandic.
            * Include common phrases that would be useful in such a setting.
            * Clearly identify speakers with labels like "Kona:" (Woman) and "Maður:" (Man)
            * After the dialogue, add 5 multiple-choice questions about details in the conversation.
            * Double-check that ALL words and structures in the dialogue strictly match the specified CEFR level.
            
            Format the dialogue clearly so I can easily extract it for audio processing.

            Your output MUST strictly follow this exact template format:


            *Saga:* [title of the dialogue]

            *Hlustaðu á þetta samtal.*

            ```
            [dialogue with speakers clearly identified as "Kona:" and "Maður:"]
            ```

            *Spurningar um samtal*

            [5 multiple-choice questions about the dialogue in Icelandic]

            *Orðabók*


            *KEY VOCABULARY:*

            ```
            * [Word in Icelandic] (grammatical info) - [Translation] - [Part of speech: noun/verb/adjective] in {user_language}]
            * [Another key word] (grammatical info) - [Translation] - [Part of speech] in {user_language}]
            * þurfa - нуждаться, требоваться - глагол
            * [Include all words that will appear in Grammar Notes section]
            ```


            *USEFUL PHRASES:*

            ```
            * [Phrase in Icelandic] - [Translation to {user_language}] - [Example of how it's used in a sentence in {user_language}]
            * [Greeting/Expression] - [Translation] - [When to use this phrase]
            ```

            *WORD COMBINATIONS:*

            ```
            * [Common word combination] - [Translation showing how meaning changes in this context]
            * [Combination using words from KEY VOCABULARY section] - [Translation and usage example]
            ```


            *GRAMMAR NOTES:*

            ```
            * [Grammatical construction from dialogue] - [Explanation in {user_language}]
            * Þurfa + að + инфинитив - выражение необходимости (используя глагол þurfa из словаря)
            * [Other grammatical notes using words already listed in KEY VOCABULARY]
            ```

            Important: Ensure all words mentioned in GRAMMAR NOTES are first included in the KEY VOCABULARY section.
            Include 15-20 items total, prioritizing practical expressions and phrases over single words.
            Avoid including very basic words that a {user_language_level} learner would already know.
            ```
            """

        start_step(get_translation("generating_content", user_language, topic=topic))
        content = await asyncio.to_thread(ai_service.generate_icelandic_test, custom_prompt)
        complete_step()

        start_step(get_translation("extracting_dialogue", user_language))
        dialogue_lines = await asyncio.to_thread(ai_service.extract_dialogue, content)
        complete_step()

        start_step(get_translation("starting_audio", user_language))
        audio_path = await asyncio.to_thread(ai_service.generate_audio_for_dialogue, dialogue_lines, user.id)
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

        # Find the markers for splitting
        dialogue_end_marker = "*Spurningar um samtal*"
        vocabulary_marker = "*Orðabók*"

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
                await update.message.reply_audio(audio_file, title="Icelandic Dialogue")

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
        await update.message.reply_text(get_translation("error_occurred", user_language, error=str(e)), parse_mode=ParseMode.MARKDOWN)

        # Delete the user's command message even if an error occurred
        await delete_user_command_message(update, context)

@restricted
@track_user_activity
async def about_story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} requested section_02 (Reading Section)")

    # Get user's language preference
    db_user = get_user_by_telegram_id(user.id)
    user_language = "English"  # Default to English if no language preference is set
    if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
        user_language = db_user.settings.language.language

    msg = await update.message.reply_text(f"```\n{get_translation('starting', user_language)}\n```", parse_mode=ParseMode.MARKDOWN_V2)

    stop_event = asyncio.Event()
    spinner_task_func, start_step, complete_step = create_spinner()
    spinner = asyncio.create_task(spinner_task_func(msg, stop_event))

    try:
        ai_service = get_ai_service()

        # Get user's language preference and language level
        db_user = get_user_by_telegram_id(user.id)
        user_language = "English"  # Default to English if no language preference is set
        user_language_level = "A2"  # Default to A2 if no language level is set
        if db_user and hasattr(db_user, 'settings') and db_user.settings:
            if db_user.settings.language:
                user_language = db_user.settings.language.language
            if db_user.settings.language_level:
                user_language_level = db_user.settings.language_level.level
        # No fallback needed anymore as language is only in settings

        start_step(get_translation("fetching_person", user_language))
        person_data = get_random_person_data()

        if not person_data:
            logger.error("Failed to fetch random person data")
            raise Exception("Failed to fetch random person data")

        complete_step()

        # Format the prompt with the person data

        start_step(get_translation("generating_content", user_language, topic=person_data['name']))

        custom_prompt = f"""
        Write a short Icelandic reading comprehension passage - 20-25 sentences long ({user_language_level} CEFR level) 
        about a person's daily life in Iceland.
        
        STRICTLY follow these guidelines for {user_language_level} level according to CEFR:
        * A1: Only use basic phrases, present tense, simple questions. Vocabulary limited to 500 most common words. Only simple sentences (subject-verb-object). Sentences should be very short (5-7 words).
        * A2: Simple past tense allowed, basic conjunctions, vocabulary up to 1000 most common words. Simple sentences with basic connectors like "og" (and), "en" (but), "því" (because).
        * B1: Some compound sentences, more verb tenses, vocabulary up to 2000 most common words. Avoid idioms and complex structures. 
        * B2: Natural flow of text, wider range of vocabulary up to 4000 words, some idioms allowed but explained in footnotes.
        * C1-C2: No restrictions on vocabulary or grammar complexity.
        
        Use the following information to guide the story:
        
        - Name: {person_data["name"]}
        - Gender: {person_data["gender"]}
        - Age: {person_data["age"]}
        - From: {person_data["origin"]}
        - Job: {person_data["job_title"]} at a {person_data["job_workplace"]}
        - Children: {person_data["number_of_children"]} children (ages {person_data["age_of_children"]})
        - Usual weekend activity: {person_data["weekend_activity"]}
        - Plan for today: {person_data["current_plan"]}
        
        Before writing the passage:
        1. Make sure to use time expressions, daily routine verbs, and family-related vocabulary appropriate for the specified level.
        
        The passage should:
        - Use vocabulary and grammar structures strictly matching the {user_language_level} level
        - Include frequently used Icelandic phrases for the level
        - Have clear paragraph breaks for readability
        - Use sentence length appropriate for the level (shorter for A1-A2, gradually longer for B1-B2)
        
        After the passage, add 5 multiple-choice comprehension questions in Icelandic with three answer choices each. 
        The questions should test understanding of where the person is from, what job they do, what time they wake up, 
        etc. Ensure that the questions and answer choices also follow the same CEFR level restrictions.
        
        Your output MUST strictly follow this exact template format:

        *Saga um [person]*

        ```
        [passage]
        ```

        *Spurningar*

        [5 multiple-choice questions about the passage in Icelandic]

        *Orðabók*


        *KEY VOCABULARY:*

        ```
        * [Word in Icelandic] (grammatical info) - [Translation] - [Part of speech: noun/verb/adjective] in {user_language}
        * [Include all words that will appear in Grammar Notes section]
        ```


        *USEFUL PHRASES:*

        ```
        * [Phrase in Icelandic] - [Translation to {user_language}] - [Example of how it's used in a sentence in {user_language}]
        * [Expression from the passage] - [Translation] - [When to use this phrase]
        ```


        *WORD COMBINATIONS:*

        ```
        * [Common word combination from the passage] - [Translation showing how meaning changes in this context]
        * [Combination using words from KEY VOCABULARY section] - [Translation and usage example]
        ```


        *GRAMMAR NOTES:*

        ```
        * [Grammatical construction from the passage] - [Explanation in {user_language}]
        * [Other grammatical notes using words already listed in KEY VOCABULARY]

        Important: Ensure all words mentioned in GRAMMAR NOTES are first included in the KEY VOCABULARY section.
        Include 15-20 items total, prioritizing practical expressions and phrases over single words.
        Avoid including very basic words that a {user_language_level} learner would already know.
        ```
        """
        content = await asyncio.to_thread(ai_service.generate_icelandic_test, custom_prompt)
        complete_step()

        stop_event.set()
        await spinner

        # Split content into parts
        # 1. Passage section
        # 2. Questions (to be sent as polls)
        # 3. Dictionary/vocabulary sections

        # Find the markers for splitting
        questions_marker = "*Spurningar*"
        vocabulary_marker = "*Orðabók*"

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

@restricted
@track_user_activity
async def communication_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} requested communication command")

    # Get user's language preference
    db_user = get_user_by_telegram_id(user.id)
    user_language = "English"  # Default to English if no language preference is set
    if db_user and hasattr(db_user, 'settings') and db_user.settings and db_user.settings.language:
        user_language = db_user.settings.language.language

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
        caption = get_translation("write_paragraph", user_language)
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
