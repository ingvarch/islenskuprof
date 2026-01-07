"""
Telegram handlers for Pimsleur lessons.
"""

import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    create_custom_lesson_request,
    get_user_custom_lessons,
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

    # Build keyboard
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
    custom_lessons = get_user_custom_lessons(db_user.id, target_lang, status="ready")
    if custom_lessons:
        keyboard.append([InlineKeyboardButton(
            f"My Custom Lessons ({len(custom_lessons)})",
            callback_data=PIMSLEUR_CUSTOM_LIST
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"*Pimsleur Icelandic Lessons*\n\n{progress_text}",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
    )


async def pimsleur_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle return to main menu."""
    query = update.callback_query
    await query.answer()

    # Re-show main menu
    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)
    target_lang = _get_target_language(db_user)
    progress = get_progress_summary(db_user.id, target_lang)
    progress_text = _format_progress_text(progress)

    keyboard = []
    if progress.get("started") and progress.get("current_lesson", 1) <= 30:
        level = progress["level"]
        lesson_num = progress["current_lesson"]
        keyboard.append([InlineKeyboardButton(
            f"Continue: {level} Lesson {lesson_num}",
            callback_data=f"{PIMSLEUR_LESSON_PREFIX}{level}_{lesson_num}"
        )])

    keyboard.append([
        InlineKeyboardButton("A1", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}A1"),
        InlineKeyboardButton("A2", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}A2"),
        InlineKeyboardButton("B1", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}B1"),
    ])
    keyboard.append([InlineKeyboardButton(
        "Create Custom Lesson",
        callback_data=PIMSLEUR_CUSTOM
    )])

    await query.edit_message_text(
        f"*Pimsleur Icelandic Lessons*\n\n{progress_text}",
        reply_markup=InlineKeyboardMarkup(keyboard),
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

    # Parse level and lesson number
    data = query.data.replace(PIMSLEUR_LESSON_PREFIX, "")
    level, lesson_num = data.split("_")
    lesson_num = int(lesson_num)

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
        logger.error(f"Error sending lesson audio: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Sorry, there was an error sending the lesson audio: {e}",
        )


async def pimsleur_complete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mark a lesson as completed."""
    query = update.callback_query

    # Parse callback data
    data = query.data.replace(PIMSLEUR_COMPLETE_PREFIX, "")
    parts = data.split("_")
    level = parts[0]
    lesson_num = int(parts[1])
    lesson_id = int(parts[2])

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

    # TODO: Trigger background generation task
    # For now, just log it
    logger.info(f"Custom lesson request {lesson_request.id} created for user {user.id}")

    return True


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
    else:
        await query.answer("Unknown action")
