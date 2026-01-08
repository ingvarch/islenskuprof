"""
Database service functions for Pimsleur lessons.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from bot.db.database import get_db_session, db_session
from bot.db.models import (
    PimsleurLesson,
    PimsleurVocabulary,
    PimsleurLessonVocabulary,
    UserPimsleurProgress,
    PimsleurCustomLesson,
    User,
)

logger = logging.getLogger(__name__)

# Valid status values for custom lessons
VALID_CUSTOM_LESSON_STATUSES = frozenset(['pending', 'generating', 'ready', 'failed'])


# ============================================================================
# Lesson queries
# ============================================================================


def get_lesson(
    language_code: str,
    level: str,
    lesson_number: int,
    session: Optional[Session] = None,
) -> Optional[PimsleurLesson]:
    """
    Get a specific Pimsleur lesson.

    Args:
        language_code: Language code (e.g., "is")
        level: Pimsleur level (1, 2, 3)
        lesson_number: Lesson number (1-30)
        session: Optional database session (for reuse within existing transaction)

    Returns:
        PimsleurLesson or None
    """
    if session is not None:
        return session.query(PimsleurLesson).filter_by(
            language_code=language_code,
            level=level,
            lesson_number=lesson_number,
        ).first()

    with db_session(auto_commit=False) as new_session:
        return new_session.query(PimsleurLesson).filter_by(
            language_code=language_code,
            level=level,
            lesson_number=lesson_number,
        ).first()


def get_lessons_for_level(
    language_code: str,
    level: str,
    generated_only: bool = True,
) -> list[PimsleurLesson]:
    """
    Get all lessons for a specific level.

    Args:
        language_code: Language code
        level: Pimsleur level (1, 2, 3)
        generated_only: If True, only return lessons with generated audio

    Returns:
        List of PimsleurLesson objects
    """
    with db_session(auto_commit=False) as session:
        query = session.query(PimsleurLesson).filter_by(
            language_code=language_code,
            level=level,
        )
        if generated_only:
            query = query.filter_by(is_generated=True)
        return query.order_by(PimsleurLesson.lesson_number).all()


def cache_telegram_file_id(lesson_id: int, file_id: str) -> None:
    """
    Cache Telegram file_id for a lesson for faster redelivery.

    Args:
        lesson_id: Lesson database ID
        file_id: Telegram file_id from sent audio
    """
    try:
        with db_session() as session:
            lesson = session.get(PimsleurLesson, lesson_id)
            if lesson:
                lesson.telegram_file_id = file_id
                lesson.updated_at = datetime.utcnow()
                logger.info(f"Cached file_id for lesson {lesson_id}")
    except Exception as e:
        logger.error(f"Failed to cache file_id: {e}")


# ============================================================================
# User progress
# ============================================================================


def get_user_progress(
    user_id: int,
    language_code: str,
) -> Optional[UserPimsleurProgress]:
    """
    Get user's Pimsleur progress for a language.

    Args:
        user_id: Database user ID
        language_code: Language code

    Returns:
        UserPimsleurProgress or None
    """
    with db_session(auto_commit=False) as session:
        return session.query(UserPimsleurProgress).filter_by(
            user_id=user_id,
            language_code=language_code,
        ).first()


def get_or_create_user_progress(
    user_id: int,
    language_code: str,
) -> UserPimsleurProgress:
    """
    Get or create user's Pimsleur progress.

    Args:
        user_id: Database user ID
        language_code: Language code

    Returns:
        UserPimsleurProgress object
    """
    with db_session() as session:
        progress = session.query(UserPimsleurProgress).filter_by(
            user_id=user_id,
            language_code=language_code,
        ).first()

        if not progress:
            progress = UserPimsleurProgress(
                user_id=user_id,
                language_code=language_code,
                level="1",
                lesson_number=1,
            )
            session.add(progress)
            logger.info(f"Created Pimsleur progress for user {user_id}")

        return progress


def get_completed_lessons(user_id: int, language_code: str) -> list[int]:
    """
    Get list of completed lesson numbers for a user.

    Args:
        user_id: Database user ID
        language_code: Language code

    Returns:
        List of completed lesson numbers
    """
    progress = get_user_progress(user_id, language_code)
    if not progress or not progress.completed_lessons:
        return []

    try:
        return json.loads(progress.completed_lessons)
    except json.JSONDecodeError:
        return []


def is_lesson_unlocked(
    user_id: int,
    language_code: str,
    level: str,
    lesson_number: int,
) -> bool:
    """
    Check if a lesson is unlocked for a user.

    A lesson is unlocked if:
    - It's lesson 1 of any level
    - All previous lessons in that level are completed
    - Previous level is completed (for level 2/3)

    Args:
        user_id: Database user ID
        language_code: Language code
        level: Pimsleur level (1, 2, 3)
        lesson_number: Lesson number

    Returns:
        True if lesson is unlocked
    """
    # Lesson 1 of Level 1 is always unlocked
    if level == "1" and lesson_number == 1:
        return True

    completed = get_completed_lessons(user_id, language_code)

    # For lesson N, need lessons 1 to N-1 completed in same level
    # We track lessons as "level_number" keys
    level_completed = [
        n for n in completed
        if 1 <= n <= 30  # Same level lessons
    ]

    if lesson_number > 1:
        # Check if previous lesson in this level is completed
        required = lesson_number - 1
        if required not in level_completed:
            return False

    return True


def mark_lesson_completed(
    user_id: int,
    language_code: str,
    level: str,
    lesson_number: int,
    lesson_id: int,
) -> None:
    """
    Mark a lesson as completed for a user.

    Args:
        user_id: Database user ID
        language_code: Language code
        level: Pimsleur level (1, 2, 3)
        lesson_number: Lesson number
        lesson_id: Lesson database ID
    """
    try:
        with db_session() as session:
            progress = session.query(UserPimsleurProgress).filter_by(
                user_id=user_id,
                language_code=language_code,
            ).first()

            if not progress:
                progress = UserPimsleurProgress(
                    user_id=user_id,
                    language_code=language_code,
                    level=level,
                    lesson_number=1,
                )
                session.add(progress)

            # Update completed lessons list
            completed = json.loads(progress.completed_lessons or "[]")
            if lesson_number not in completed:
                completed.append(lesson_number)
                completed.sort()
            progress.completed_lessons = json.dumps(completed)

            # Update current position
            progress.level = level
            progress.lesson_number = lesson_number + 1 if lesson_number < 30 else 30
            progress.last_lesson_id = lesson_id

            # Update streak (if completed within 48 hours of last completion)
            previous_completed_at = progress.last_completed_at
            progress.last_completed_at = datetime.utcnow()

            if previous_completed_at:
                time_since_last = datetime.utcnow() - previous_completed_at
                if time_since_last < timedelta(hours=48):
                    progress.streak_count = (progress.streak_count or 0) + 1
                else:
                    progress.streak_count = 1
            else:
                progress.streak_count = 1

            # Add lesson duration to total time
            lesson = session.get(PimsleurLesson, lesson_id)
            if lesson:
                progress.total_time_seconds = (progress.total_time_seconds or 0) + lesson.duration_seconds

            progress.updated_at = datetime.utcnow()

            logger.info(
                f"Marked lesson {level} L{lesson_number} completed for user {user_id}"
            )
    except Exception as e:
        logger.error(f"Failed to mark lesson completed: {e}")
        raise


def get_progress_summary(user_id: int, language_code: str) -> dict:
    """
    Get a summary of user's Pimsleur progress.

    Args:
        user_id: Database user ID
        language_code: Language code

    Returns:
        Dictionary with progress summary
    """
    progress = get_user_progress(user_id, language_code)

    if not progress:
        return {
            "started": False,
            "level": "1",
            "current_lesson": 1,
            "completed_count": 0,
            "streak": 0,
            "total_time_minutes": 0,
        }

    completed = json.loads(progress.completed_lessons or "[]")

    return {
        "started": True,
        "level": progress.level,
        "current_lesson": progress.lesson_number,
        "completed_count": len(completed),
        "streak": progress.streak_count,
        "total_time_minutes": progress.total_time_seconds // 60,
        "last_completed": progress.last_completed_at.isoformat() if progress.last_completed_at else None,
    }


# ============================================================================
# Custom lessons
# ============================================================================


def create_custom_lesson_request(
    user_id: int,
    language_code: str,
    title: str,
    source_text: str,
) -> PimsleurCustomLesson:
    """
    Create a new custom lesson request.

    Args:
        user_id: Database user ID
        language_code: Language code
        title: Lesson title
        source_text: User-provided text

    Returns:
        PimsleurCustomLesson object
    """
    with db_session() as session:
        lesson = PimsleurCustomLesson(
            user_id=user_id,
            language_code=language_code,
            title=title,
            source_text=source_text,
        )
        session.add(lesson)
        session.flush()
        session.refresh(lesson)
        logger.info(f"Created custom lesson request {lesson.id} for user {user_id}")
        # Expunge to allow access outside session
        session.expunge(lesson)
        return lesson


def get_user_custom_lessons(
    user_id: int,
    language_code: str,
    status: Optional[str] = None,
) -> list[PimsleurCustomLesson]:
    """
    Get user's custom lessons.

    Args:
        user_id: Database user ID
        language_code: Language code
        status: Optional filter by status

    Returns:
        List of PimsleurCustomLesson objects
    """
    with db_session(auto_commit=False) as session:
        query = session.query(PimsleurCustomLesson).filter_by(
            user_id=user_id,
            language_code=language_code,
        )
        if status:
            query = query.filter_by(status=status)
        return query.order_by(PimsleurCustomLesson.created_at.desc()).all()


def update_custom_lesson_status(
    lesson_id: int,
    status: str,
    script_json: Optional[str] = None,
    audio_path: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    vocabulary_json: Optional[str] = None,
) -> None:
    """
    Update custom lesson status and generated content.

    Args:
        lesson_id: Custom lesson ID
        status: New status (pending, generating, ready, failed)
        script_json: Generated script JSON
        audio_path: Path to generated audio
        duration_seconds: Audio duration
        vocabulary_json: Vocabulary JSON

    Raises:
        ValueError: If status is not a valid value
    """
    if status not in VALID_CUSTOM_LESSON_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(VALID_CUSTOM_LESSON_STATUSES)}")

    try:
        with db_session() as session:
            lesson = session.get(PimsleurCustomLesson, lesson_id)
            if lesson:
                lesson.status = status
                if script_json:
                    lesson.script_json = script_json
                if audio_path:
                    lesson.audio_file_path = audio_path
                if duration_seconds:
                    lesson.duration_seconds = duration_seconds
                if vocabulary_json:
                    lesson.vocabulary_json = vocabulary_json
                lesson.updated_at = datetime.utcnow()
                logger.info(f"Updated custom lesson {lesson_id} status to {status}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to update custom lesson: {e}")


def get_custom_lesson_by_id(
    lesson_id: int,
    user_id: int,
) -> Optional[PimsleurCustomLesson]:
    """
    Get a custom lesson by ID, verifying ownership.

    Args:
        lesson_id: Custom lesson database ID
        user_id: Database user ID (for ownership verification)

    Returns:
        PimsleurCustomLesson or None if not found or not owned by user
    """
    with db_session(auto_commit=False) as session:
        lesson = session.get(PimsleurCustomLesson, lesson_id)
        if lesson and lesson.user_id == user_id:
            return lesson
        return None


def cache_custom_lesson_file_id(lesson_id: int, file_id: str) -> None:
    """
    Cache Telegram file_id for a custom lesson.

    Args:
        lesson_id: Custom lesson database ID
        file_id: Telegram file ID
    """
    try:
        with db_session() as session:
            lesson = session.get(PimsleurCustomLesson, lesson_id)
            if lesson:
                lesson.telegram_file_id = file_id
                logger.info(f"Cached file_id for custom lesson {lesson_id}")
    except Exception as e:
        logger.error(f"Failed to cache custom lesson file_id: {e}")


# ============================================================================
# Custom lesson wizard functions (added for UX improvement)
# ============================================================================


def create_custom_lesson_with_settings(
    user_id: int,
    language_code: str,
    title: str,
    source_text: str,
    focus: str = "vocabulary",
    voice_preference: str = "both",
    difficulty_level: str = "auto",
    text_analysis_json: Optional[str] = None,
) -> PimsleurCustomLesson:
    """
    Create a new custom lesson with wizard settings.

    Args:
        user_id: Database user ID
        language_code: Language code (e.g., "is")
        title: Lesson title
        source_text: User-provided text
        focus: Lesson focus ("vocabulary", "pronunciation", "dialogue")
        voice_preference: Voice preference ("female", "male", "both")
        difficulty_level: Difficulty level ("1", "2", "3", "auto")
        text_analysis_json: Cached text analysis results

    Returns:
        PimsleurCustomLesson object (detached from session)
    """
    with db_session() as session:
        lesson = PimsleurCustomLesson(
            user_id=user_id,
            language_code=language_code,
            title=title,
            source_text=source_text,
            focus=focus,
            voice_preference=voice_preference,
            difficulty_level=difficulty_level,
            text_analysis_json=text_analysis_json,
        )
        session.add(lesson)
        session.flush()
        session.refresh(lesson)
        lesson_id = lesson.id  # Capture ID before expunge
        logger.info(
            f"Created custom lesson {lesson_id} for user {user_id} "
            f"(focus={focus}, voice={voice_preference}, level={difficulty_level})"
        )
        # Expunge to allow access outside session
        session.expunge(lesson)
        return lesson


def update_custom_lesson_generation_status(
    lesson_id: int,
    status: str,
    error_message: Optional[str] = None,
    script_json: Optional[str] = None,
    audio_path: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    vocabulary_json: Optional[str] = None,
) -> None:
    """
    Update custom lesson generation status with timing and error tracking.

    Args:
        lesson_id: Custom lesson database ID
        status: New status (pending, generating, ready, failed)
        error_message: Error message for failed status
        script_json: Generated script JSON
        audio_path: Path to generated audio
        duration_seconds: Audio duration
        vocabulary_json: Vocabulary JSON
    """
    if status not in VALID_CUSTOM_LESSON_STATUSES:
        raise ValueError(f"Invalid status '{status}'")

    try:
        with db_session() as session:
            lesson = session.get(PimsleurCustomLesson, lesson_id)
            if not lesson:
                logger.warning(f"Custom lesson {lesson_id} not found for status update")
                return

            lesson.status = status
            lesson.updated_at = datetime.utcnow()

            # Track generation timing
            if status == "generating" and not lesson.generation_started_at:
                lesson.generation_started_at = datetime.utcnow()
            elif status in ("ready", "failed"):
                lesson.generation_completed_at = datetime.utcnow()

            # Update content fields
            if error_message is not None:
                lesson.error_message = error_message[:500] if error_message else None
            if script_json is not None:
                lesson.script_json = script_json
            if audio_path is not None:
                lesson.audio_file_path = audio_path
            if duration_seconds is not None:
                lesson.duration_seconds = duration_seconds
            if vocabulary_json is not None:
                lesson.vocabulary_json = vocabulary_json

            logger.info(f"Updated custom lesson {lesson_id} status to {status}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Failed to update custom lesson status: {e}")
        raise


def delete_custom_lesson(lesson_id: int, user_id: int) -> bool:
    """
    Delete a custom lesson (only if owned by user).

    Args:
        lesson_id: Custom lesson database ID
        user_id: Database user ID (for ownership verification)

    Returns:
        True if deleted, False if not found or not owned
    """
    try:
        with db_session() as session:
            lesson = session.get(PimsleurCustomLesson, lesson_id)
            if lesson and lesson.user_id == user_id:
                session.delete(lesson)
                logger.info(f"Deleted custom lesson {lesson_id} for user {user_id}")
                return True
            logger.warning(f"Custom lesson {lesson_id} not found or not owned by user {user_id}")
            return False
    except Exception as e:
        logger.error(f"Failed to delete custom lesson: {e}")
        return False


def retry_custom_lesson(lesson_id: int, user_id: int) -> Optional[PimsleurCustomLesson]:
    """
    Reset a failed custom lesson for retry.

    Args:
        lesson_id: Custom lesson database ID
        user_id: Database user ID (for ownership verification)

    Returns:
        Updated PimsleurCustomLesson or None if not found/not owned
    """
    try:
        with db_session() as session:
            lesson = session.get(PimsleurCustomLesson, lesson_id)
            if not lesson or lesson.user_id != user_id:
                logger.warning(f"Custom lesson {lesson_id} not found or not owned by user {user_id}")
                return None

            if lesson.status != "failed":
                logger.warning(f"Cannot retry lesson {lesson_id} with status {lesson.status}")
                return None

            # Reset to pending state
            lesson.status = "pending"
            lesson.error_message = None
            lesson.generation_started_at = None
            lesson.generation_completed_at = None
            lesson.script_json = None
            lesson.audio_file_path = None
            lesson.telegram_file_id = None
            lesson.duration_seconds = None
            lesson.vocabulary_json = None
            lesson.updated_at = datetime.utcnow()

            session.flush()
            session.refresh(lesson)
            logger.info(f"Reset custom lesson {lesson_id} for retry")
            # Expunge to allow access outside session
            session.expunge(lesson)
            return lesson
    except Exception as e:
        logger.error(f"Failed to retry custom lesson: {e}")
        return None


def get_custom_lesson_count(user_id: int, language_code: str) -> dict:
    """
    Get count of custom lessons by status for a user.

    Args:
        user_id: Database user ID
        language_code: Language code

    Returns:
        Dictionary with counts by status
    """
    with db_session(auto_commit=False) as session:
        lessons = session.query(PimsleurCustomLesson).filter_by(
            user_id=user_id,
            language_code=language_code,
        ).all()

        counts = {"total": 0, "pending": 0, "generating": 0, "ready": 0, "failed": 0}
        for lesson in lessons:
            counts["total"] += 1
            if lesson.status in counts:
                counts[lesson.status] += 1

        return counts
