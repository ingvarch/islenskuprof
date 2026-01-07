"""
Telegram handlers for Pimsleur lessons.
"""

import asyncio
import json
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest

from bot.utils.access_control import restricted
from bot.utils.user_tracking import track_user_activity
from bot.db.user_service import get_user_by_telegram_id
from bot.db.pimsleur_service import (
    get_lesson,
    get_lessons_for_level,
    get_or_create_user_progress,
    get_completed_lessons,
    is_lesson_unlocked,
    mark_lesson_completed,
    get_progress_summary,
    cache_telegram_file_id,
    cache_custom_lesson_file_id,
    create_custom_lesson_request,
    get_user_custom_lessons,
    get_custom_lesson_by_id,
    update_custom_lesson_status,
)

logger = logging.getLogger(__name__)

# Callback data prefixes
PIMSLEUR_MENU = "pimsleur_menu"
PIMSLEUR_LEVEL_PREFIX = "pimsleur_level_"
PIMSLEUR_LESSON_PREFIX = "pimsleur_lesson_"
PIMSLEUR_COMPLETE_PREFIX = "pimsleur_complete_"
PIMSLEUR_CUSTOM = "pimsleur_custom"
PIMSLEUR_CUSTOM_LIST = "pimsleur_custom_list"
PIMSLEUR_LOCKED = "pimsleur_locked"


def _get_target_language(db_user) -> str:
    """Get user's target language code."""
    if db_user and db_user.settings and db_user.settings.target_language:
        return db_user.settings.target_language.code
    return "is"  # Default to Icelandic


def _format_progress_text(progress: dict) -> str:
    """Format progress summary for display."""
    if not progress.get("started"):
        return "You haven't started any lessons yet.\nChoose a level to begin!"

    text = f"*Current Progress*\n"
    text += f"Level: {progress['level']}\n"
    text += f"Next Lesson: {progress['current_lesson']}\n"
    text += f"Completed: {progress['completed_count']} lessons\n"

    if progress.get("streak", 0) > 1:
        text += f"Streak: {progress['streak']} days\n"

    if progress.get("total_time_minutes", 0) > 0:
        hours = progress["total_time_minutes"] // 60
        mins = progress["total_time_minutes"] % 60
        text += f"Total time: {hours}h {mins}m\n"

    return text


def _build_main_menu_keyboard(progress: dict, db_user_id: int, target_lang: str) -> InlineKeyboardMarkup:
    """Build the main Pimsleur menu keyboard."""
    keyboard = []

    # Continue button if user has progress
    if progress.get("started") and progress.get("current_lesson", 1) <= 30:
        level = progress["level"]
        lesson_num = progress["current_lesson"]
        keyboard.append([InlineKeyboardButton(
            f"Continue: {level} Lesson {lesson_num}",
            callback_data=f"{PIMSLEUR_LESSON_PREFIX}{level}_{lesson_num}"
        )])

    # Level selection buttons
    keyboard.append([
        InlineKeyboardButton("A1", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}A1"),
        InlineKeyboardButton("A2", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}A2"),
        InlineKeyboardButton("B1", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}B1"),
    ])

    # Custom lesson option
    keyboard.append([InlineKeyboardButton(
        "Create Custom Lesson",
        callback_data=PIMSLEUR_CUSTOM
    )])

    # My custom lessons (if any exist)
    custom_lessons = get_user_custom_lessons(db_user_id, target_lang, status="ready")
    if custom_lessons:
        keyboard.append([InlineKeyboardButton(
            f"My Custom Lessons ({len(custom_lessons)})",
            callback_data=PIMSLEUR_CUSTOM_LIST
        )])

    return InlineKeyboardMarkup(keyboard)


@restricted
@track_user_activity
async def pimsleur_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pimsleur command - show Pimsleur lesson menu."""
    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)

    if not db_user:
        await update.message.reply_text(
            "Please use /start first to initialize your account."
        )
        return

    target_lang = _get_target_language(db_user)
    progress = get_progress_summary(db_user.id, target_lang)
    progress_text = _format_progress_text(progress)
    reply_markup = _build_main_menu_keyboard(progress, db_user.id, target_lang)

    await update.message.reply_text(
        f"*Pimsleur Icelandic Lessons*\n\n{progress_text}",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
    )


async def pimsleur_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle return to main menu."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)
    target_lang = _get_target_language(db_user)
    progress = get_progress_summary(db_user.id, target_lang)
    progress_text = _format_progress_text(progress)
    reply_markup = _build_main_menu_keyboard(progress, db_user.id, target_lang)

    await query.edit_message_text(
        f"*Pimsleur Icelandic Lessons*\n\n{progress_text}",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
    )


async def pimsleur_level_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show lessons grid for a specific level."""
    query = update.callback_query
    await query.answer()

    level = query.data.replace(PIMSLEUR_LEVEL_PREFIX, "")
    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)
    target_lang = _get_target_language(db_user)

    # Get completed lessons
    completed = get_completed_lessons(db_user.id, target_lang)

    # Get available lessons
    available_lessons = get_lessons_for_level(target_lang, level, generated_only=True)
    available_nums = {l.lesson_number for l in available_lessons}

    # Build lesson grid (6 rows x 5 columns = 30 lessons)
    keyboard = []
    for row in range(6):
        row_buttons = []
        for col in range(5):
            lesson_num = row * 5 + col + 1
            is_completed = lesson_num in completed
            is_available = lesson_num in available_nums
            is_unlocked = is_lesson_unlocked(db_user.id, target_lang, level, lesson_num)

            if is_completed:
                emoji = "V"  # Completed
            elif is_unlocked and is_available:
                emoji = ""  # Unlocked
            else:
                emoji = "X"  # Locked

            if is_unlocked and is_available:
                callback = f"{PIMSLEUR_LESSON_PREFIX}{level}_{lesson_num}"
            else:
                callback = PIMSLEUR_LOCKED

            row_buttons.append(InlineKeyboardButton(
                f"{emoji}{lesson_num}",
                callback_data=callback
            ))
        keyboard.append(row_buttons)

    # Back button
    keyboard.append([InlineKeyboardButton("Back", callback_data=PIMSLEUR_MENU)])

    level_names = {"A1": "Beginner", "A2": "Elementary", "B1": "Intermediate"}
    try:
        await query.edit_message_text(
            f"*{level} - {level_names.get(level, '')}*\n\n"
            f"V = completed, X = locked\n"
            f"Select a lesson to start:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def pimsleur_lesson_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deliver a Pimsleur lesson."""
    query = update.callback_query
    await query.answer("Loading lesson...")

    # Parse level and lesson number with validation
    data = query.data.replace(PIMSLEUR_LESSON_PREFIX, "")
    parts = data.split("_")
    if len(parts) < 2:
        await query.answer("Invalid lesson data", show_alert=True)
        return

    try:
        level = parts[0]
        lesson_num = int(parts[1])
    except (ValueError, IndexError):
        await query.answer("Invalid lesson data", show_alert=True)
        return

    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)
    target_lang = _get_target_language(db_user)

    # Check if lesson is unlocked
    if not is_lesson_unlocked(db_user.id, target_lang, level, lesson_num):
        await query.edit_message_text(
            f"Lesson {lesson_num} is locked.\n"
            f"Complete the previous lessons first!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}{level}")
            ]]),
        )
        return

    # Get the lesson
    lesson = get_lesson(target_lang, level, lesson_num)

    if not lesson or not lesson.is_generated:
        await query.edit_message_text(
            f"Sorry, {level} Lesson {lesson_num} is not yet available.\n"
            f"Please try another lesson.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}{level}")
            ]]),
        )
        return

    # Send lesson info
    duration_min = lesson.duration_seconds // 60
    await query.edit_message_text(
        f"*{level} Lesson {lesson_num}*\n"
        f"*{lesson.title}*\n\n"
        f"Duration: {duration_min} minutes\n"
        f"{lesson.description or ''}\n\n"
        "Sending audio...",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Send audio file
    try:
        if lesson.telegram_file_id:
            # Use cached file_id for fast delivery
            message = await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=lesson.telegram_file_id,
                title=f"{level} L{lesson_num}: {lesson.title}",
                performer="Islenskuprof Pimsleur",
            )
        else:
            # Upload from file path
            with open(lesson.audio_file_path, "rb") as audio_file:
                message = await context.bot.send_audio(
                    chat_id=update.effective_chat.id,
                    audio=audio_file,
                    title=f"{level} L{lesson_num}: {lesson.title}",
                    performer="Islenskuprof Pimsleur",
                )
                # Cache the file_id
                if message.audio and message.audio.file_id:
                    cache_telegram_file_id(lesson.id, message.audio.file_id)

        # Send vocabulary summary
        vocab = json.loads(lesson.vocabulary_json) if lesson.vocabulary_json else []
        if vocab:
            vocab_text = "*Vocabulary in this lesson:*\n"
            for item in vocab[:15]:  # Limit to 15 items
                word = item.get("word", item.get("word_target", ""))
                translation = item.get("translation", item.get("word_native", ""))
                if word and translation:
                    vocab_text += f"- {word}: {translation}\n"

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=vocab_text,
                parse_mode=ParseMode.MARKDOWN,
            )

        # Send completion button
        keyboard = [[InlineKeyboardButton(
            "Mark as Complete",
            callback_data=f"{PIMSLEUR_COMPLETE_PREFIX}{level}_{lesson_num}_{lesson.id}"
        )]]
        keyboard.append([InlineKeyboardButton(
            "Back to Lessons",
            callback_data=f"{PIMSLEUR_LEVEL_PREFIX}{level}"
        )])

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Listen to the entire lesson, then mark it complete to unlock the next one.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        logger.error(f"Error sending lesson audio: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, there was an error sending the lesson audio. Please try again later.",
        )


async def pimsleur_complete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mark a lesson as completed."""
    query = update.callback_query

    # Parse callback data with validation
    data = query.data.replace(PIMSLEUR_COMPLETE_PREFIX, "")
    parts = data.split("_")
    if len(parts) < 3:
        await query.answer("Invalid callback data", show_alert=True)
        return

    try:
        level = parts[0]
        lesson_num = int(parts[1])
        lesson_id = int(parts[2])
    except (ValueError, IndexError):
        await query.answer("Invalid lesson data", show_alert=True)
        return

    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)
    target_lang = _get_target_language(db_user)

    try:
        mark_lesson_completed(db_user.id, target_lang, level, lesson_num, lesson_id)
        await query.answer("Lesson marked as complete!")

        # Show congratulations and next steps
        next_lesson = lesson_num + 1 if lesson_num < 30 else None

        if next_lesson:
            text = (
                f"*{level} Lesson {lesson_num} completed!*\n\n"
                f"Great job! Lesson {next_lesson} is now unlocked."
            )
            keyboard = [[InlineKeyboardButton(
                f"Start Lesson {next_lesson}",
                callback_data=f"{PIMSLEUR_LESSON_PREFIX}{level}_{next_lesson}"
            )]]
        else:
            text = (
                f"*{level} Lesson {lesson_num} completed!*\n\n"
                f"Congratulations! You've completed all {level} lessons!"
            )
            keyboard = []

        keyboard.append([InlineKeyboardButton(
            "Back to Menu",
            callback_data=PIMSLEUR_MENU
        )])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        logger.error(f"Error marking lesson complete: {e}")
        await query.answer(f"Error: {e}", show_alert=True)


async def pimsleur_locked_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle clicks on locked lessons."""
    query = update.callback_query
    await query.answer(
        "This lesson is locked. Complete the previous lessons first!",
        show_alert=True
    )


async def pimsleur_custom_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start custom lesson creation process."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "*Create Custom Pimsleur Lesson*\n\n"
        "Send me a text in Icelandic (50-500 words) that you want to learn.\n"
        "I will create a Pimsleur-style lesson from it.\n\n"
        "Good sources:\n"
        "- News article paragraphs\n"
        "- Story excerpts\n"
        "- Song lyrics\n"
        "- Dialogue transcripts\n\n"
        "Reply with your text (or /cancel to go back):",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Set conversation state
    context.user_data["awaiting_pimsleur_text"] = True


async def _generate_custom_lesson_background(
    bot: Bot,
    telegram_user_id: int,
    lesson_id: int,
    language_code: str,
    source_text: str,
    title: str,
) -> None:
    """
    Background task to generate a custom Pimsleur lesson.

    Args:
        bot: Telegram bot instance for sending notifications
        telegram_user_id: Telegram user ID for notifications
        lesson_id: Custom lesson database ID
        language_code: Language code
        source_text: User-provided text
        title: Lesson title
    """
    from bot.languages import get_language_config_by_code
    from bot.pimsleur.generator import PimsleurLessonGenerator
    from bot.pimsleur.audio_assembler import PimsleurAudioAssembler

    logger.info(f"Starting background generation for custom lesson {lesson_id}")

    try:
        # Update status to generating
        update_custom_lesson_status(lesson_id, status="generating")

        # Get language config
        lang_config = get_language_config_by_code(language_code)

        # Generate script (run in thread pool to avoid blocking)
        logger.info(f"Generating script for custom lesson {lesson_id}")
        generator = PimsleurLessonGenerator(lang_config)
        script = await asyncio.to_thread(
            generator.generate_custom_lesson_script, source_text
        )

        # Save script
        script_json = json.dumps(script, ensure_ascii=False)

        # Generate audio (run in thread pool)
        logger.info(f"Generating audio for custom lesson {lesson_id}")
        output_dir = Path("data/pimsleur") / language_code / "custom"
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / f"custom_{lesson_id}.mp3"

        assembler = PimsleurAudioAssembler(language_code)
        await asyncio.to_thread(
            assembler.generate_lesson_audio,
            script,
            str(audio_path),
        )

        # Calculate duration
        duration = script.get("calculated_duration", 900)

        # Update database with results
        update_custom_lesson_status(
            lesson_id=lesson_id,
            status="ready",
            script_json=script_json,
            audio_path=str(audio_path),
            duration_seconds=duration,
            vocabulary_json=json.dumps(script.get("vocabulary_summary", []), ensure_ascii=False),
        )

        logger.info(f"Custom lesson {lesson_id} generated successfully")

        # Notify user
        await bot.send_message(
            chat_id=telegram_user_id,
            text=f"Your custom lesson *{title}* is ready!\n\n"
                 f"Use /pimsleur and go to 'My Custom Lessons' to access it.",
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        logger.error(f"Failed to generate custom lesson {lesson_id}: {e}")

        # Update status to failed
        update_custom_lesson_status(lesson_id, status="failed")

        # Notify user
        await bot.send_message(
            chat_id=telegram_user_id,
            text=f"Sorry, failed to generate your custom lesson.\n"
                 f"Error: {str(e)[:100]}",
        )


async def handle_pimsleur_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle text input for custom lesson creation.

    Returns True if the message was handled, False otherwise.
    """
    if not context.user_data.get("awaiting_pimsleur_text"):
        return False

    user = update.effective_user
    text = update.message.text

    # Check for cancel
    if text.lower() == "/cancel":
        context.user_data["awaiting_pimsleur_text"] = False
        await update.message.reply_text(
            "Custom lesson creation cancelled.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back to Menu", callback_data=PIMSLEUR_MENU)
            ]]),
        )
        return True

    # Validate text length
    word_count = len(text.split())
    if word_count < 50:
        await update.message.reply_text(
            f"Text is too short ({word_count} words). Please provide at least 50 words."
        )
        return True

    if word_count > 1000:
        await update.message.reply_text(
            f"Text is too long ({word_count} words). Please keep it under 1000 words."
        )
        return True

    context.user_data["awaiting_pimsleur_text"] = False

    # Create custom lesson request
    db_user = get_user_by_telegram_id(user.id)
    target_lang = _get_target_language(db_user)

    # Generate title from first few words
    title = " ".join(text.split()[:5]) + "..."

    lesson_request = create_custom_lesson_request(
        user_id=db_user.id,
        language_code=target_lang,
        title=title,
        source_text=text,
    )

    await update.message.reply_text(
        "*Custom lesson request created!*\n\n"
        "Your lesson is being generated. This may take 5-10 minutes.\n"
        "I'll notify you when it's ready.\n\n"
        f"Request ID: {lesson_request.id}",
        parse_mode=ParseMode.MARKDOWN,
    )

    # Trigger background generation task
    logger.info(f"Custom lesson request {lesson_request.id} created for user {user.id}")
    asyncio.create_task(
        _generate_custom_lesson_background(
            bot=context.bot,
            telegram_user_id=user.id,
            lesson_id=lesson_request.id,
            language_code=target_lang,
            source_text=text,
            title=title,
        )
    )

    return True


async def pimsleur_custom_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show list of user's custom lessons."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)
    target_lang = _get_target_language(db_user)

    # Get all custom lessons
    custom_lessons = get_user_custom_lessons(db_user.id, target_lang)

    if not custom_lessons:
        try:
            await query.edit_message_text(
                "You don't have any custom lessons yet.\n\n"
                "Use 'Create Custom Lesson' to generate one from your text!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Create Custom Lesson", callback_data=PIMSLEUR_CUSTOM),
                    InlineKeyboardButton("Back", callback_data=PIMSLEUR_MENU),
                ]]),
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
        return

    # Build lesson list
    keyboard = []
    for lesson in custom_lessons:
        status_emoji = {
            "pending": "⏳",
            "generating": "🔄",
            "ready": "✅",
            "failed": "❌",
        }.get(lesson.status, "❓")

        if lesson.status == "ready":
            callback = f"pimsleur_custom_play_{lesson.id}"
        else:
            callback = PIMSLEUR_CUSTOM_LIST  # Just refresh

        keyboard.append([InlineKeyboardButton(
            f"{status_emoji} {lesson.title[:30]}",
            callback_data=callback,
        )])

    keyboard.append([
        InlineKeyboardButton("Create New", callback_data=PIMSLEUR_CUSTOM),
        InlineKeyboardButton("Back", callback_data=PIMSLEUR_MENU),
    ])

    try:
        await query.edit_message_text(
            "*My Custom Lessons*\n\n"
            "✅ = ready, ⏳ = pending, 🔄 = generating, ❌ = failed\n\n"
            "Tap a ready lesson to play:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def pimsleur_custom_play_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Play a custom lesson."""
    query = update.callback_query
    await query.answer("Loading custom lesson...")

    # Parse lesson ID with validation
    try:
        lesson_id = int(query.data.replace("pimsleur_custom_play_", ""))
    except ValueError:
        await query.answer("Invalid lesson ID", show_alert=True)
        return

    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)

    # Get lesson by ID (verifies ownership)
    lesson = get_custom_lesson_by_id(lesson_id, db_user.id)

    if not lesson:
        await query.edit_message_text(
            "Lesson not found.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back", callback_data=PIMSLEUR_CUSTOM_LIST)
            ]]),
        )
        return

    if lesson.status != "ready":
        await query.edit_message_text(
            f"Lesson is not ready yet (status: {lesson.status}).",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back", callback_data=PIMSLEUR_CUSTOM_LIST)
            ]]),
        )
        return

    # Send audio
    try:
        if lesson.telegram_file_id:
            await query.message.reply_audio(
                audio=lesson.telegram_file_id,
                title=lesson.title,
                caption=f"*{lesson.title}*\nCustom Pimsleur Lesson",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            audio_path = Path(lesson.audio_file_path)
            if audio_path.exists():
                with open(audio_path, "rb") as audio_file:
                    message = await query.message.reply_audio(
                        audio=audio_file,
                        title=lesson.title,
                        caption=f"*{lesson.title}*\nCustom Pimsleur Lesson",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    # Cache file_id for future use
                    if message.audio:
                        cache_custom_lesson_file_id(lesson_id, message.audio.file_id)
            else:
                logger.error(f"Audio file not found: {audio_path}")
                await query.message.reply_text(
                    "Audio file not found. Please try again later."
                )
                return

        await query.edit_message_text(
            f"*{lesson.title}*\n\nEnjoy your custom lesson!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back to Custom Lessons", callback_data=PIMSLEUR_CUSTOM_LIST)
            ]]),
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        logger.error(f"Error sending custom lesson audio: {e}", exc_info=True)
        await query.edit_message_text(
            "Error loading lesson. Please try again later.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back", callback_data=PIMSLEUR_CUSTOM_LIST)
            ]]),
        )


# Handler dispatcher for all pimsleur callbacks
async def pimsleur_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route pimsleur callbacks to appropriate handlers."""
    query = update.callback_query
    data = query.data

    if data == PIMSLEUR_MENU:
        await pimsleur_menu_callback(update, context)
    elif data.startswith(PIMSLEUR_LEVEL_PREFIX):
        await pimsleur_level_callback(update, context)
    elif data.startswith(PIMSLEUR_LESSON_PREFIX):
        await pimsleur_lesson_callback(update, context)
    elif data.startswith(PIMSLEUR_COMPLETE_PREFIX):
        await pimsleur_complete_callback(update, context)
    elif data == PIMSLEUR_LOCKED:
        await pimsleur_locked_callback(update, context)
    elif data == PIMSLEUR_CUSTOM:
        await pimsleur_custom_callback(update, context)
    elif data == PIMSLEUR_CUSTOM_LIST:
        await pimsleur_custom_list_callback(update, context)
    elif data.startswith("pimsleur_custom_play_"):
        await pimsleur_custom_play_callback(update, context)
    else:
        await query.answer("Unknown action")
