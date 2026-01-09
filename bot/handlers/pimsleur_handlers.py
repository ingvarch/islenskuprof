"""
Telegram handlers for Pimsleur lessons.

Includes a multi-step wizard for custom lesson creation with:
- Text analysis and vocabulary preview
- Title customization
- Lesson settings (focus, voice, difficulty)
- Real-time progress tracking during generation
"""

import asyncio
import json
import logging
from datetime import date
from enum import Enum
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
    get_level_unlock_status,
    is_lesson_unlocked,
    mark_lesson_completed,
    get_progress_summary,
    cache_telegram_file_id,
    cache_custom_lesson_file_id,
    get_user_custom_lessons,
    get_custom_lesson_by_id,
    get_custom_lesson_count,
    update_custom_lesson_status,
    create_custom_lesson_with_settings,
    update_custom_lesson_generation_status,
    delete_custom_lesson,
    retry_custom_lesson,
)
from bot.pimsleur.text_analyzer import TextAnalyzer
from bot.pimsleur.vocabulary_manager import VocabularyProgressionManager
from bot.pimsleur.lesson_formatter import (
    format_header_message,
    format_vocabulary_message,
    format_grammar_message,
    format_simple_vocabulary,
    format_custom_lesson_header,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Level format conversion helpers
# ============================================================================


def _level_to_db_format(level: str) -> str:
    """Convert UI level (1, 2, 3) to database format (L1, L2, L3)."""
    if level.startswith("L"):
        return level  # Already in DB format
    return f"L{level}"


def _level_from_db_format(level: str) -> str:
    """Convert database level (L1, L2, L3) to UI format (1, 2, 3)."""
    if level.startswith("L"):
        return level[1:]
    return level


# ============================================================================
# Wizard State Management
# ============================================================================


class WizardState(str, Enum):
    """States for the custom lesson creation wizard."""

    IDLE = "idle"
    AWAITING_TEXT = "awaiting_text"
    TEXT_ANALYSIS = "text_analysis"
    VOCABULARY_PREVIEW = "vocabulary_preview"
    TITLE_INPUT = "title_input"
    SETTINGS = "settings"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


# Progress tracking stages
PROGRESS_STAGES = {
    "initializing": {"label": "Initializing...", "percent": 5},
    "analyzing": {"label": "Analyzing text...", "percent": 10},
    "generating_script": {"label": "Creating lesson script...", "percent": 25},
    "vocabulary": {"label": "Processing vocabulary...", "percent": 40},
    "generating_audio": {"label": "Generating audio...", "percent": 50},
    "audio_segments": {"label": "Recording segments...", "percent": 70},
    "finalizing": {"label": "Finalizing lesson...", "percent": 95},
    "complete": {"label": "Complete!", "percent": 100},
}

PROGRESS_UPDATE_INTERVAL = 12  # seconds


def _get_wizard_data(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Get wizard data from context, initializing if needed."""
    if "custom_wizard" not in context.user_data:
        context.user_data["custom_wizard"] = {
            "state": WizardState.IDLE,
            "source_text": None,
            "analysis": None,
            "title": None,
            "settings": {
                "focus": "vocabulary",
                "voice": "both",
                "difficulty": "auto",
            },
            "lesson_id": None,
            "message_id": None,
            "progress": {"stage": "initializing", "percent": 0},
        }
    return context.user_data["custom_wizard"]


def _clear_wizard_data(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear wizard data from context."""
    context.user_data.pop("custom_wizard", None)
    context.user_data.pop("awaiting_pimsleur_text", None)
    context.user_data.pop("awaiting_title_input", None)


def _format_progress_bar(percent: int, width: int = 10) -> str:
    """Create a text-based progress bar."""
    filled = int(width * percent / 100)
    empty = width - filled
    return "[" + "\u2588" * filled + "\u2591" * empty + f"] {percent}%"


def _format_vocabulary_preview(vocabulary: list[dict], limit: int = 15) -> str:
    """Format vocabulary list for display in a code block."""
    if not vocabulary:
        return "```\nNo vocabulary extracted\n```"

    lines = []
    for item in vocabulary[:limit]:
        word = item.get("word", "")
        count = item.get("count", 1)
        freq_marker = " *" if item.get("is_frequent") else ""
        lines.append(f"- {word} ({count}x){freq_marker}")

    if len(vocabulary) > limit:
        lines.append(f"...and {len(vocabulary) - limit} more")

    return "```\n" + "\n".join(lines) + "\n```"


# Callback data prefixes - Standard lesson flow
PIMSLEUR_MENU = "pimsleur_menu"
PIMSLEUR_LEVEL_PREFIX = "pimsleur_level_"
PIMSLEUR_LESSON_PREFIX = "pimsleur_lesson_"
PIMSLEUR_COMPLETE_PREFIX = "pimsleur_complete_"
PIMSLEUR_CUSTOM = "pimsleur_custom"
PIMSLEUR_CUSTOM_LIST = "pimsleur_custom_list"
PIMSLEUR_LOCKED = "pimsleur_locked"

# Callback data prefixes - Custom lesson wizard
WIZARD_CANCEL = "pimsleur_wiz_cancel"
WIZARD_BACK = "pimsleur_wiz_back"
WIZARD_CONTINUE = "pimsleur_wiz_continue"
WIZARD_VIEW_VOCAB = "pimsleur_wiz_vocab"
WIZARD_EDIT_TITLE = "pimsleur_wiz_edit_title"
WIZARD_USE_TITLE = "pimsleur_wiz_use_title"
WIZARD_FOCUS_PREFIX = "pimsleur_wiz_focus_"
WIZARD_VOICE_PREFIX = "pimsleur_wiz_voice_"
WIZARD_DIFF_PREFIX = "pimsleur_wiz_diff_"

# Valid values for wizard settings (for validation)
VALID_FOCUS_VALUES = {"vocabulary", "pronunciation", "dialogue"}
VALID_VOICE_VALUES = {"female", "male", "both"}
VALID_DIFFICULTY_VALUES = {"1", "2", "3", "auto"}
WIZARD_CONFIRM = "pimsleur_wiz_confirm"
WIZARD_RETRY_PREFIX = "pimsleur_wiz_retry_"
WIZARD_DELETE_PREFIX = "pimsleur_wiz_delete_"
WIZARD_PLAY_PREFIX = "pimsleur_wiz_play_"


def _get_target_language(db_user) -> str:
    """Get user's target language code."""
    if db_user and db_user.settings and db_user.settings.target_language:
        return db_user.settings.target_language.code
    return "is"  # Default to Icelandic


def _format_progress_text(progress: dict) -> str:
    """Format progress summary for display."""
    if not progress.get("started"):
        return "You haven't started any lessons yet.\nChoose a level to begin!"

    text = "*Current Progress*\n"
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


def _build_main_menu_keyboard(
    progress: dict, db_user_id: int, target_lang: str
) -> InlineKeyboardMarkup:
    """Build the main Pimsleur menu keyboard."""
    keyboard = []

    # Continue button if user has progress
    if progress.get("started") and progress.get("current_lesson", 1) <= 30:
        level = progress["level"]
        lesson_num = progress["current_lesson"]
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"Continue: {level} Lesson {lesson_num}",
                    callback_data=f"{PIMSLEUR_LESSON_PREFIX}{level}_{lesson_num}",
                )
            ]
        )

    # Level selection buttons
    keyboard.append(
        [
            InlineKeyboardButton("Level 1", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}1"),
            InlineKeyboardButton("Level 2", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}2"),
            InlineKeyboardButton("Level 3", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}3"),
        ]
    )

    # Custom lesson option
    keyboard.append(
        [InlineKeyboardButton("Create Custom Lesson", callback_data=PIMSLEUR_CUSTOM)]
    )

    # My custom lessons (if any exist)
    custom_lessons = get_user_custom_lessons(db_user_id, target_lang, status="ready")
    if custom_lessons:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"My Custom Lessons ({len(custom_lessons)})",
                    callback_data=PIMSLEUR_CUSTOM_LIST,
                )
            ]
        )

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


async def pimsleur_menu_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
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


async def pimsleur_level_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show lessons grid for a specific level."""
    query = update.callback_query
    await query.answer()

    level = query.data.replace(PIMSLEUR_LEVEL_PREFIX, "")
    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)
    target_lang = _get_target_language(db_user)

    # OPTIMIZED: Get all status info in 2 queries instead of 32
    status = get_level_unlock_status(db_user.id, target_lang, level)
    completed = status["completed_set"]
    generated_nums = status["generated_set"]

    # Build lesson grid dynamically (5 buttons per row)
    keyboard = []
    row_buttons = []
    for unit_num in range(1, 31):
        is_completed = unit_num in completed
        is_generated = unit_num in generated_nums
        # Calculate unlock status in memory (no DB query)
        is_unlocked = unit_num == 1 or (unit_num - 1) in completed

        if is_completed:
            emoji = "\u2713"  # Checkmark for completed
        elif is_unlocked and is_generated:
            emoji = ""  # Available - no emoji
        else:
            emoji = "\U0001f512"  # Lock emoji for locked

        if is_unlocked and is_generated:
            callback = f"{PIMSLEUR_LESSON_PREFIX}{level}_{unit_num}"
        else:
            callback = PIMSLEUR_LOCKED

        row_buttons.append(
            InlineKeyboardButton(f"{emoji}{unit_num}", callback_data=callback)
        )

        # 5 buttons per row
        if len(row_buttons) == 5:
            keyboard.append(row_buttons)
            row_buttons = []

    # Add remaining buttons
    if row_buttons:
        keyboard.append(row_buttons)

    # Back button
    keyboard.append([InlineKeyboardButton("Back", callback_data=PIMSLEUR_MENU)])

    level_names = {"1": "Beginner", "2": "Elementary", "3": "Intermediate"}
    units_text = (
        f"{len(generated_nums)} units available" if generated_nums else "No units yet"
    )
    try:
        await query.edit_message_text(
            f"*Level {level} - {level_names.get(level, '')}*\n\n"
            f"{units_text}\n"
            f"Select a unit to start:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def pimsleur_lesson_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
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
            f"Lesson {lesson_num} is locked.\nComplete the previous lessons first!",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Back", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}{level}"
                        )
                    ]
                ]
            ),
        )
        return

    # Get the lesson (convert level to DB format)
    db_level = _level_to_db_format(level)
    lesson = get_lesson(target_lang, db_level, lesson_num)

    if not lesson or not lesson.is_generated:
        await query.edit_message_text(
            f"Sorry, Level {level} Unit {lesson_num} is not yet available.\n"
            f"Please try another lesson.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Back", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}{level}"
                        )
                    ]
                ]
            ),
        )
        return

    # Try to get rich display data from vocabulary banks
    numeric_level = int(level) if level.isdigit() else 1
    vocab_manager = VocabularyProgressionManager(language_code=target_lang)
    display_data = vocab_manager.get_lesson_display_data(numeric_level, lesson_num)

    try:
        # Update message to show loading
        await query.edit_message_text(
            f"*Level {level} Unit {lesson_num}*\n*{lesson.title}*\n\nSending audio...",
            parse_mode=ParseMode.MARKDOWN,
        )

        # 1. Send audio file FIRST
        if lesson.telegram_file_id:
            message = await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=lesson.telegram_file_id,
                title=f"{level} L{lesson_num}: {lesson.title}",
                performer="Islenskuprof Pimsleur",
            )
        else:
            with open(lesson.audio_file_path, "rb") as audio_file:
                message = await context.bot.send_audio(
                    chat_id=update.effective_chat.id,
                    audio=audio_file,
                    title=f"{level} L{lesson_num}: {lesson.title}",
                    performer="Islenskuprof Pimsleur",
                )
                if message.audio and message.audio.file_id:
                    cache_telegram_file_id(lesson.id, message.audio.file_id)

        # 2. Send lesson info messages
        if display_data:
            # Rich format: Header + Dialogue
            header_msg = format_header_message(
                display_data, numeric_level, lesson_num, target_lang
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=header_msg,
                parse_mode=ParseMode.MARKDOWN,
            )

            # Vocabulary + Phrases
            vocab_msg = format_vocabulary_message(display_data, target_lang)
            if vocab_msg:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=vocab_msg,
                    parse_mode=ParseMode.MARKDOWN,
                )

            # Grammar + Meta
            grammar_msg = format_grammar_message(display_data, lesson.duration_seconds)
            if grammar_msg:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=grammar_msg,
                    parse_mode=ParseMode.MARKDOWN,
                )
        else:
            # Fallback: simple format when no vocabulary bank exists
            vocab = json.loads(lesson.vocabulary_json) if lesson.vocabulary_json else []
            if vocab:
                vocab_text = format_simple_vocabulary(vocab)
                if vocab_text:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=vocab_text,
                        parse_mode=ParseMode.MARKDOWN,
                    )

        # 3. Send completion button
        keyboard = [
            [
                InlineKeyboardButton(
                    "Mark as Complete",
                    callback_data=f"{PIMSLEUR_COMPLETE_PREFIX}{level}_{lesson_num}_{lesson.id}",
                )
            ]
        ]
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Back to Lessons", callback_data=f"{PIMSLEUR_LEVEL_PREFIX}{level}"
                )
            ]
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Listen to the entire lesson, then mark it complete to unlock the next one.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        logger.error(f"Error sending lesson: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, there was an error sending the lesson. Please try again later.",
        )


async def pimsleur_complete_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
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
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"Start Lesson {next_lesson}",
                        callback_data=f"{PIMSLEUR_LESSON_PREFIX}{level}_{next_lesson}",
                    )
                ]
            ]
        else:
            text = (
                f"*{level} Lesson {lesson_num} completed!*\n\n"
                f"Congratulations! You've completed all {level} lessons!"
            )
            keyboard = []

        keyboard.append(
            [InlineKeyboardButton("Back to Menu", callback_data=PIMSLEUR_MENU)]
        )

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        logger.error(f"Error marking lesson complete: {e}")
        await query.answer(f"Error: {e}", show_alert=True)


async def pimsleur_locked_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle clicks on locked lessons."""
    query = update.callback_query
    await query.answer(
        "This lesson is locked. Complete the previous lessons first!", show_alert=True
    )


async def pimsleur_custom_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Start custom lesson creation wizard - Step 1: Request text input."""
    query = update.callback_query
    await query.answer()

    # Check for existing wizard in progress
    wizard = _get_wizard_data(context)
    if wizard["state"] not in (
        WizardState.IDLE,
        WizardState.COMPLETED,
        WizardState.FAILED,
    ):
        await query.answer(
            "You already have a lesson creation in progress. Cancel it first.",
            show_alert=True,
        )
        return

    # Initialize wizard state
    _clear_wizard_data(context)
    wizard = _get_wizard_data(context)
    wizard["state"] = WizardState.AWAITING_TEXT

    await query.edit_message_text(
        "*Create Custom Pimsleur Lesson*\n\n"
        "Send me a text in your target language (50-1000 words).\n\n"
        "*Good sources:*\n"
        "- News articles\n"
        "- Story excerpts\n"
        "- Song lyrics\n"
        "- Dialogues or conversations\n\n"
        "_Reply with your text or tap Cancel._",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancel", callback_data=WIZARD_CANCEL)]]
        ),
        parse_mode=ParseMode.MARKDOWN,
    )

    # Set text input flag
    context.user_data["awaiting_pimsleur_text"] = True


async def _generate_custom_lesson_background(
    bot: Bot,
    telegram_user_id: int,
    lesson_id: int,
    language_code: str,
    source_text: str,
    title: str,
    difficulty_level: str = "1",
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
        difficulty_level: Difficulty level (1, 2, or 3)
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
            generator.generate_custom_lesson_script, source_text, difficulty_level
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
            vocabulary_json=json.dumps(
                script.get("vocabulary_summary", []), ensure_ascii=False
            ),
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


async def handle_pimsleur_text_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """
    Handle text input for custom lesson wizard - Step 2: Analyze text.

    Returns True if the message was handled, False otherwise.
    """
    # Check for text input mode (wizard Step 1)
    if not context.user_data.get("awaiting_pimsleur_text"):
        # Check for title input mode (wizard title step)
        if context.user_data.get("awaiting_title_input"):
            return await _handle_title_input(update, context)
        return False

    user = update.effective_user
    text = update.message.text

    # Check for cancel
    if text.lower() == "/cancel":
        _clear_wizard_data(context)
        await update.message.reply_text(
            "Custom lesson creation cancelled.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Back to Menu", callback_data=PIMSLEUR_MENU)]]
            ),
        )
        return True

    # Validate text length
    word_count = len(text.split())
    if word_count < 50:
        await update.message.reply_text(
            f"Text is too short ({word_count} words). Please provide at least 50 words.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Cancel", callback_data=WIZARD_CANCEL)]]
            ),
        )
        return True

    if word_count > 1000:
        await update.message.reply_text(
            f"Text is too long ({word_count} words). Please keep it under 1000 words.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Cancel", callback_data=WIZARD_CANCEL)]]
            ),
        )
        return True

    context.user_data["awaiting_pimsleur_text"] = False

    # Get user's target language
    db_user = get_user_by_telegram_id(user.id)
    target_lang = _get_target_language(db_user)

    # Analyze text
    analyzer = TextAnalyzer(target_lang)
    analysis = analyzer.analyze(text)

    # Generate default title: #N - DD-MM-YYYY
    lesson_counts = get_custom_lesson_count(db_user.id, target_lang)
    next_number = lesson_counts.get("total", 0) + 1
    today = date.today().strftime("%d-%m-%Y")
    default_title = f"#{next_number} - {today}"

    # Update wizard state
    wizard = _get_wizard_data(context)
    wizard["state"] = WizardState.TEXT_ANALYSIS
    wizard["source_text"] = text
    wizard["analysis"] = analysis
    wizard["title"] = default_title

    # Show analysis results (Step 2)
    stats_text = (
        f"📊 *Text Analysis*\n\n"
        f"📝 {analysis['word_count']} words total\n"
        f"🔤 {analysis['unique_words']} unique words\n"
        f"📚 ~{analysis['estimated_lesson_words']} words for lesson\n"
        f"📈 Difficulty level: {analysis['detected_difficulty']}\n\n"
        f"*Default title:*\n"
        f"`{default_title}`"
    )

    keyboard = [
        [InlineKeyboardButton("View Vocabulary", callback_data=WIZARD_VIEW_VOCAB)],
        [InlineKeyboardButton("Continue", callback_data=WIZARD_CONTINUE)],
        [InlineKeyboardButton("Cancel", callback_data=WIZARD_CANCEL)],
    ]

    await update.message.reply_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )

    return True


async def _handle_title_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """Handle custom title input from user."""
    text = update.message.text.strip()

    if text.lower() == "/cancel":
        context.user_data["awaiting_title_input"] = False
        # Return to settings step
        wizard = _get_wizard_data(context)
        wizard["state"] = WizardState.TEXT_ANALYSIS
        await update.message.reply_text(
            "Title change cancelled.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Continue", callback_data=WIZARD_CONTINUE)]]
            ),
        )
        return True

    # Validate title length
    if len(text) > 200:
        await update.message.reply_text(
            "Title is too long. Please keep it under 200 characters."
        )
        return True

    if len(text) < 3:
        await update.message.reply_text(
            "Title is too short. Please provide at least 3 characters."
        )
        return True

    # Update wizard with new title
    wizard = _get_wizard_data(context)
    wizard["title"] = text
    context.user_data["awaiting_title_input"] = False

    await update.message.reply_text(
        f"*Title updated:* {text}\n\nTap Continue to proceed to settings.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Continue", callback_data=WIZARD_CONTINUE)]]
        ),
        parse_mode=ParseMode.MARKDOWN,
    )

    return True


async def pimsleur_custom_list_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show list of user's custom lessons with status-appropriate actions."""
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
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Create Custom Lesson", callback_data=PIMSLEUR_CUSTOM
                            ),
                            InlineKeyboardButton("Back", callback_data=PIMSLEUR_MENU),
                        ]
                    ]
                ),
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
        return

    # Build lesson list with status-appropriate actions
    keyboard = []
    for lesson in custom_lessons:
        status_emoji = {
            "pending": "\u23f3",  # hourglass
            "generating": "\U0001f504",  # arrows
            "ready": "\u2705",  # checkmark
            "failed": "\u274c",  # x
        }.get(lesson.status, "\u2753")  # question

        title_display = (
            lesson.title[:25] + "..." if len(lesson.title) > 25 else lesson.title
        )

        if lesson.status == "ready":
            # Play button for ready lessons
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{status_emoji} {title_display}",
                        callback_data=f"pimsleur_custom_play_{lesson.id}",
                    )
                ]
            )
        elif lesson.status == "failed":
            # Retry and Delete for failed lessons
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{status_emoji} {title_display}",
                        callback_data=f"{WIZARD_RETRY_PREFIX}{lesson.id}",
                    ),
                    InlineKeyboardButton(
                        "\U0001f5d1",  # wastebasket
                        callback_data=f"{WIZARD_DELETE_PREFIX}{lesson.id}",
                    ),
                ]
            )
        else:
            # Pending/generating - just show status
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{status_emoji} {title_display}",
                        callback_data=PIMSLEUR_CUSTOM_LIST,  # Refresh
                    )
                ]
            )

    keyboard.append(
        [
            InlineKeyboardButton("Create New", callback_data=PIMSLEUR_CUSTOM),
            InlineKeyboardButton("Back", callback_data=PIMSLEUR_MENU),
        ]
    )

    try:
        await query.edit_message_text(
            "*My Custom Lessons*\n\n"
            "\u2705 = ready (tap to play)\n"
            "\u23f3 = pending, \U0001f504 = generating\n"
            "\u274c = failed (tap to retry, \U0001f5d1 to delete)",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def pimsleur_custom_play_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Play a custom lesson with full display data."""
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
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Back", callback_data=PIMSLEUR_CUSTOM_LIST)]]
            ),
        )
        return

    if lesson.status != "ready":
        await query.edit_message_text(
            f"Lesson is not ready yet (status: {lesson.status}).",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Back", callback_data=PIMSLEUR_CUSTOM_LIST)]]
            ),
        )
        return

    # Extract display data from script
    display_data = None
    if lesson.script_json:
        try:
            script = json.loads(lesson.script_json)
            display_data = script.get("display_data")
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse script_json for lesson {lesson_id}")

    chat_id = update.effective_chat.id

    try:
        # Update message to show loading
        await query.edit_message_text(
            f"*{lesson.title}*\n\nSending audio...",
            parse_mode=ParseMode.MARKDOWN,
        )

        # 1. Send audio file FIRST (same as pre-built lessons)
        if lesson.telegram_file_id:
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=lesson.telegram_file_id,
                title=lesson.title,
                performer="Custom Lesson",
            )
        else:
            audio_path = Path(lesson.audio_file_path)
            if audio_path.exists():
                with open(audio_path, "rb") as audio_file:
                    message = await context.bot.send_audio(
                        chat_id=chat_id,
                        audio=audio_file,
                        title=lesson.title,
                        performer="Custom Lesson",
                    )
                    # Cache file_id for future use
                    if message.audio and message.audio.file_id:
                        cache_custom_lesson_file_id(lesson_id, message.audio.file_id)
            else:
                logger.error(f"Audio file not found: {audio_path}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Audio file not found. Please try again later.",
                )
                return

        # 2. Send display messages if available
        if display_data:
            # Header with opening dialogue
            header_msg = format_custom_lesson_header(display_data, lesson.language_code)
            if header_msg:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=header_msg,
                    parse_mode=ParseMode.MARKDOWN,
                )

            # Vocabulary and phrases
            vocab_msg = format_vocabulary_message(display_data, lesson.language_code)
            if vocab_msg:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=vocab_msg,
                    parse_mode=ParseMode.MARKDOWN,
                )

            # Grammar notes
            grammar_msg = format_grammar_message(
                display_data, lesson.duration_seconds or 900
            )
            if grammar_msg:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=grammar_msg,
                    parse_mode=ParseMode.MARKDOWN,
                )

        # 3. Send completion button
        await context.bot.send_message(
            chat_id=chat_id,
            text="Enjoy your custom lesson!",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Back to Custom Lessons", callback_data=PIMSLEUR_CUSTOM_LIST
                        )
                    ]
                ]
            ),
        )

    except Exception as e:
        logger.error(f"Error sending custom lesson audio: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, there was an error sending the lesson. Please try again later.",
        )


# ============================================================================
# Wizard Callback Handlers
# ============================================================================


async def wizard_cancel_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Cancel the custom lesson wizard."""
    query = update.callback_query
    await query.answer()

    _clear_wizard_data(context)

    await query.edit_message_text(
        "Custom lesson creation cancelled.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Back to Menu", callback_data=PIMSLEUR_MENU)]]
        ),
    )


async def wizard_view_vocab_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show vocabulary preview - Step 3."""
    query = update.callback_query
    await query.answer()

    wizard = _get_wizard_data(context)
    analysis = wizard.get("analysis", {})
    vocabulary = analysis.get("vocabulary_preview", [])

    vocab_text = _format_vocabulary_preview(vocabulary, limit=20)

    await query.edit_message_text(
        f"*Vocabulary Preview*\n\n"
        f"Words to be included in the lesson:\n\n"
        f"{vocab_text}\n\n"
        f"_\\* = appears frequently_",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Back", callback_data=WIZARD_BACK)],
                [InlineKeyboardButton("Continue", callback_data=WIZARD_CONTINUE)],
            ]
        ),
        parse_mode=ParseMode.MARKDOWN,
    )

    wizard["state"] = WizardState.VOCABULARY_PREVIEW


async def wizard_back_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Go back to previous wizard step."""
    query = update.callback_query
    await query.answer()

    wizard = _get_wizard_data(context)
    state = wizard["state"]

    # Navigate back based on current state
    if state == WizardState.VOCABULARY_PREVIEW:
        # Back to analysis
        wizard["state"] = WizardState.TEXT_ANALYSIS
        analysis = wizard.get("analysis", {})

        current_title = wizard.get("title", "Untitled")
        stats_text = (
            f"📊 *Text Analysis*\n\n"
            f"📝 {analysis.get('word_count', 0)} words total\n"
            f"🔤 {analysis.get('unique_words', 0)} unique words\n"
            f"📚 ~{analysis.get('estimated_lesson_words', 15)} words for lesson\n"
            f"📈 Difficulty level: {analysis.get('detected_difficulty', '1')}\n\n"
            f"*Default title:*\n"
            f"`{current_title}`"
        )

        keyboard = [
            [InlineKeyboardButton("View Vocabulary", callback_data=WIZARD_VIEW_VOCAB)],
            [InlineKeyboardButton("Continue", callback_data=WIZARD_CONTINUE)],
            [InlineKeyboardButton("Cancel", callback_data=WIZARD_CANCEL)],
        ]

        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )

    elif state == WizardState.SETTINGS:
        # Back to title selection
        wizard["state"] = WizardState.TEXT_ANALYSIS
        await _show_title_step(query, wizard)

    else:
        # Default: go to menu
        await query.edit_message_text(
            "Returning to menu...",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Back to Menu", callback_data=PIMSLEUR_MENU)]]
            ),
        )


async def _show_title_step(query, wizard: dict) -> None:
    """Show title editing step."""
    title = wizard.get("title", "Untitled")

    await query.edit_message_text(
        f"*Lesson Title*\n\n"
        f"Suggested: _{title}_\n\n"
        f"Would you like to use this title or enter your own?",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Use This Title", callback_data=WIZARD_USE_TITLE
                    )
                ],
                [InlineKeyboardButton("Edit Title", callback_data=WIZARD_EDIT_TITLE)],
                [InlineKeyboardButton("Back", callback_data=WIZARD_BACK)],
            ]
        ),
        parse_mode=ParseMode.MARKDOWN,
    )


async def wizard_continue_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Continue to next wizard step."""
    query = update.callback_query
    await query.answer()

    wizard = _get_wizard_data(context)
    state = wizard["state"]

    if state in (WizardState.TEXT_ANALYSIS, WizardState.VOCABULARY_PREVIEW):
        # Continue to title step
        await _show_title_step(query, wizard)

    elif state == WizardState.TITLE_INPUT:
        # Continue to settings step
        await _show_settings_step(query, wizard)

    else:
        # Unknown state, show error
        await query.answer("Please start again.", show_alert=True)


async def wizard_use_title_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Use the suggested title and continue to settings."""
    query = update.callback_query
    await query.answer()

    wizard = _get_wizard_data(context)
    await _show_settings_step(query, wizard)


async def wizard_edit_title_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Switch to title input mode."""
    query = update.callback_query
    await query.answer()

    wizard = _get_wizard_data(context)
    wizard["state"] = WizardState.TITLE_INPUT
    context.user_data["awaiting_title_input"] = True

    await query.edit_message_text(
        "*Edit Title*\n\n"
        "Type your custom title (3-200 characters).\n"
        "Or type /cancel to keep the suggested title.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def _show_settings_step(query, wizard: dict) -> None:
    """Show the settings step."""
    wizard["state"] = WizardState.SETTINGS
    settings = wizard.get("settings", {})

    # Current settings display
    focus = settings.get("focus", "vocabulary")
    voice = settings.get("voice", "both")
    difficulty = settings.get("difficulty", "auto")

    # Focus options
    focus_display = {
        "vocabulary": "Vocabulary",
        "pronunciation": "Pronunciation",
        "dialogue": "Dialogue",
    }

    # Voice options
    voice_display = {
        "female": "Female",
        "male": "Male",
        "both": "Both",
    }

    # Build keyboard
    keyboard = []

    # Focus row
    focus_row = []
    for f in ["vocabulary", "pronunciation", "dialogue"]:
        label = focus_display[f]
        if f == focus:
            label = f"\u2713 {label}"  # checkmark
        focus_row.append(
            InlineKeyboardButton(label, callback_data=f"{WIZARD_FOCUS_PREFIX}{f}")
        )
    keyboard.append(focus_row)

    # Voice row
    voice_row = []
    for v in ["female", "male", "both"]:
        label = voice_display[v]
        if v == voice:
            label = f"\u2713 {label}"
        voice_row.append(
            InlineKeyboardButton(label, callback_data=f"{WIZARD_VOICE_PREFIX}{v}")
        )
    keyboard.append(voice_row)

    # Difficulty row
    diff_row = []
    diff_labels = {"1": "L1", "2": "L2", "3": "L3"}
    for d in ["1", "2", "3", "auto"]:
        label = diff_labels.get(d, d) if d != "auto" else "Auto"
        if d == difficulty:
            label = f"\u2713 {label}"
        diff_row.append(
            InlineKeyboardButton(label, callback_data=f"{WIZARD_DIFF_PREFIX}{d}")
        )
    keyboard.append(diff_row)

    # Action buttons
    keyboard.append(
        [InlineKeyboardButton("\u2705 Create Lesson", callback_data=WIZARD_CONFIRM)]
    )
    keyboard.append(
        [
            InlineKeyboardButton("Back", callback_data=WIZARD_BACK),
            InlineKeyboardButton("Cancel", callback_data=WIZARD_CANCEL),
        ]
    )

    await query.edit_message_text(
        f"*Lesson Settings*\n\n"
        f"*Title:* {wizard.get('title', 'Untitled')}\n\n"
        f"Select your preferences:\n\n"
        f"*Focus:*\n"
        f"*Voice:*\n"
        f"*Difficulty:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )


async def wizard_focus_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Update focus setting."""
    query = update.callback_query
    focus = query.data.replace(WIZARD_FOCUS_PREFIX, "")

    if focus not in VALID_FOCUS_VALUES:
        logger.warning(f"Invalid focus value received: {focus}")
        await query.answer("Invalid option", show_alert=True)
        return

    wizard = _get_wizard_data(context)
    wizard["settings"]["focus"] = focus
    await query.answer(f"Focus: {focus.title()}")
    await _show_settings_step(query, wizard)


async def wizard_voice_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Update voice setting."""
    query = update.callback_query
    voice = query.data.replace(WIZARD_VOICE_PREFIX, "")

    if voice not in VALID_VOICE_VALUES:
        logger.warning(f"Invalid voice value received: {voice}")
        await query.answer("Invalid option", show_alert=True)
        return

    wizard = _get_wizard_data(context)
    wizard["settings"]["voice"] = voice
    await query.answer(f"Voice: {voice.title()}")
    await _show_settings_step(query, wizard)


async def wizard_difficulty_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Update difficulty setting."""
    query = update.callback_query
    difficulty = query.data.replace(WIZARD_DIFF_PREFIX, "")

    if difficulty not in VALID_DIFFICULTY_VALUES:
        logger.warning(f"Invalid difficulty value received: {difficulty}")
        await query.answer("Invalid option", show_alert=True)
        return

    wizard = _get_wizard_data(context)
    wizard["settings"]["difficulty"] = difficulty
    await query.answer(f"Difficulty: {difficulty}")
    await _show_settings_step(query, wizard)


async def wizard_confirm_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Confirm and start lesson generation."""
    query = update.callback_query
    await query.answer("Starting generation...")

    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)
    target_lang = _get_target_language(db_user)

    wizard = _get_wizard_data(context)
    settings = wizard.get("settings", {})
    analysis = wizard.get("analysis", {})

    # Determine effective difficulty
    difficulty = settings.get("difficulty", "auto")
    if difficulty == "auto":
        difficulty = analysis.get("detected_difficulty", "1")

    # Create lesson in database with settings
    lesson = create_custom_lesson_with_settings(
        user_id=db_user.id,
        language_code=target_lang,
        title=wizard.get("title", "Custom Lesson"),
        source_text=wizard.get("source_text", ""),
        focus=settings.get("focus", "vocabulary"),
        voice_preference=settings.get("voice", "both"),
        difficulty_level=difficulty,
        text_analysis_json=json.dumps(analysis),
    )

    wizard["lesson_id"] = lesson.id
    wizard["state"] = WizardState.GENERATING

    # Show initial progress
    progress_text = (
        f"*Generating Your Custom Lesson*\n\n"
        f"{_format_progress_bar(5)}\n\n"
        f"Initializing...\n\n"
        f"_This may take 5-10 minutes. You'll be notified when ready._"
    )

    msg = await query.edit_message_text(
        progress_text,
        parse_mode=ParseMode.MARKDOWN,
    )

    wizard["message_id"] = msg.message_id

    # Start background generation with progress tracking
    asyncio.create_task(
        _generate_custom_lesson_with_progress(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            telegram_user_id=user.id,
            lesson_id=lesson.id,
            language_code=target_lang,
            source_text=wizard.get("source_text", ""),
            title=wizard.get("title", "Custom Lesson"),
            difficulty_level=difficulty,
            settings=settings,
            user_data=context.user_data,
        )
    )


async def _generate_custom_lesson_with_progress(
    bot: Bot,
    chat_id: int,
    message_id: int,
    telegram_user_id: int,
    lesson_id: int,
    language_code: str,
    source_text: str,
    title: str,
    difficulty_level: str,
    settings: dict,
    user_data: dict,
) -> None:
    """Background task with progress updates."""
    from bot.languages import get_language_config_by_code
    from bot.pimsleur.generator import PimsleurLessonGenerator
    from bot.pimsleur.audio_assembler import PimsleurAudioAssembler

    async def update_progress(stage: str, extra_text: str = "") -> None:
        """Update progress message."""
        stage_info = PROGRESS_STAGES.get(stage, {"label": stage, "percent": 50})
        progress_bar = _format_progress_bar(stage_info["percent"])

        text = (
            f"*Generating Your Custom Lesson*\n\n"
            f"{progress_bar}\n\n"
            f"{stage_info['label']}\n"
            f"{extra_text}\n\n"
            f"_This may take 5-10 minutes._"
        )

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.warning(f"Progress update failed: {e}")

    try:
        await update_progress("initializing")
        update_custom_lesson_generation_status(lesson_id, status="generating")

        await update_progress("analyzing")
        lang_config = get_language_config_by_code(language_code)

        await update_progress("generating_script")
        generator = PimsleurLessonGenerator(lang_config)
        script = await asyncio.to_thread(
            generator.generate_custom_lesson_script, source_text, difficulty_level
        )

        await update_progress("vocabulary")
        script_json = json.dumps(script, ensure_ascii=False)

        await update_progress("generating_audio")
        output_dir = Path("data/pimsleur") / language_code / "custom"
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / f"custom_{lesson_id}.mp3"

        assembler = PimsleurAudioAssembler(language_code)

        await update_progress("audio_segments", "_This step takes the longest..._")
        await asyncio.to_thread(
            assembler.generate_lesson_audio,
            script,
            str(audio_path),
        )

        await update_progress("finalizing")
        duration = script.get("calculated_duration", 900)

        update_custom_lesson_generation_status(
            lesson_id=lesson_id,
            status="ready",
            script_json=script_json,
            audio_path=str(audio_path),
            duration_seconds=duration,
            vocabulary_json=json.dumps(
                script.get("vocabulary_summary", []), ensure_ascii=False
            ),
        )

        await update_progress("complete")

        # Update wizard state
        if "custom_wizard" in user_data:
            user_data["custom_wizard"]["state"] = WizardState.COMPLETED

        # Final success message with play button
        duration_min = duration // 60
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=(
                f"\u2705 *Lesson Ready!*\n\n"
                f"*{title}*\n"
                f"\u23f1 {duration_min} minutes\n\n"
                f"Tap below to listen:"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "\u25b6\ufe0f Play Now",
                            callback_data=f"pimsleur_custom_play_{lesson_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "My Custom Lessons", callback_data=PIMSLEUR_CUSTOM_LIST
                        )
                    ],
                ]
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        logger.error(
            f"Failed to generate custom lesson {lesson_id}: {e}", exc_info=True
        )

        # Update wizard state
        if "custom_wizard" in user_data:
            user_data["custom_wizard"]["state"] = WizardState.FAILED
            user_data["custom_wizard"]["error"] = str(e)

        update_custom_lesson_generation_status(
            lesson_id, status="failed", error_message=str(e)[:500]
        )

        # Error message with retry option
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=(
                f"\u274c *Generation Failed*\n\n"
                f"Error: {str(e)[:200]}\n\n"
                f"You can retry or delete this lesson from 'My Custom Lessons'."
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "\U0001f504 Retry",
                            callback_data=f"{WIZARD_RETRY_PREFIX}{lesson_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "My Custom Lessons", callback_data=PIMSLEUR_CUSTOM_LIST
                        )
                    ],
                ]
            ),
            parse_mode=ParseMode.MARKDOWN,
        )


async def wizard_retry_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Retry a failed lesson generation."""
    query = update.callback_query

    try:
        lesson_id = int(query.data.replace(WIZARD_RETRY_PREFIX, ""))
    except ValueError:
        await query.answer("Invalid lesson ID", show_alert=True)
        return

    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)

    # Reset the lesson for retry
    lesson = retry_custom_lesson(lesson_id, db_user.id)
    if not lesson:
        await query.answer("Lesson not found or cannot be retried", show_alert=True)
        return

    await query.answer("Retrying generation...")

    # Show progress
    msg = await query.edit_message_text(
        f"*Retrying Generation*\n\n"
        f"{_format_progress_bar(5)}\n\n"
        f"Initializing...\n\n"
        f"_This may take 5-10 minutes._",
        parse_mode=ParseMode.MARKDOWN,
    )

    target_lang = _get_target_language(db_user)

    # Start generation
    asyncio.create_task(
        _generate_custom_lesson_with_progress(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            telegram_user_id=user.id,
            lesson_id=lesson_id,
            language_code=target_lang,
            source_text=lesson.source_text,
            title=lesson.title,
            difficulty_level=lesson.difficulty_level,
            settings={
                "focus": lesson.focus,
                "voice": lesson.voice_preference,
                "difficulty": lesson.difficulty_level,
            },
            user_data=context.user_data,
        )
    )


async def wizard_delete_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Delete a custom lesson."""
    query = update.callback_query

    try:
        lesson_id = int(query.data.replace(WIZARD_DELETE_PREFIX, ""))
    except ValueError:
        await query.answer("Invalid lesson ID", show_alert=True)
        return

    user = update.effective_user
    db_user = get_user_by_telegram_id(user.id)

    success = delete_custom_lesson(lesson_id, db_user.id)
    if success:
        await query.answer("Lesson deleted")
        # Refresh the list
        await pimsleur_custom_list_callback(update, context)
    else:
        await query.answer("Failed to delete lesson", show_alert=True)


# Handler dispatcher for all pimsleur callbacks
async def pimsleur_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Route pimsleur callbacks to appropriate handlers."""
    query = update.callback_query
    data = query.data

    # Standard lesson flow
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

    # Wizard callbacks
    elif data == WIZARD_CANCEL:
        await wizard_cancel_callback(update, context)
    elif data == WIZARD_BACK:
        await wizard_back_callback(update, context)
    elif data == WIZARD_CONTINUE:
        await wizard_continue_callback(update, context)
    elif data == WIZARD_VIEW_VOCAB:
        await wizard_view_vocab_callback(update, context)
    elif data == WIZARD_EDIT_TITLE:
        await wizard_edit_title_callback(update, context)
    elif data == WIZARD_USE_TITLE:
        await wizard_use_title_callback(update, context)
    elif data.startswith(WIZARD_FOCUS_PREFIX):
        await wizard_focus_callback(update, context)
    elif data.startswith(WIZARD_VOICE_PREFIX):
        await wizard_voice_callback(update, context)
    elif data.startswith(WIZARD_DIFF_PREFIX):
        await wizard_difficulty_callback(update, context)
    elif data == WIZARD_CONFIRM:
        await wizard_confirm_callback(update, context)
    elif data.startswith(WIZARD_RETRY_PREFIX):
        await wizard_retry_callback(update, context)
    elif data.startswith(WIZARD_DELETE_PREFIX):
        await wizard_delete_callback(update, context)

    else:
        await query.answer("Unknown action")
