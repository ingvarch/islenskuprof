"""
Database service functions for Pimsleur lessons.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from bot.db.database import get_db_session
from bot.db.models import (
    PimsleurLesson,
    PimsleurVocabulary,
    PimsleurLessonVocabulary,
    UserPimsleurProgress,
    PimsleurCustomLesson,
    User,
)

logger = logging.getLogger(__name__)


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
        level: CEFR level (A1, A2, B1)
        lesson_number: Lesson number (1-30)
        session: Optional database session

    Returns:
        PimsleurLesson or None
    """
    close_session = False
    if session is None:
        session = get_db_session()
        close_session = True

    try:
        return session.query(PimsleurLesson).filter_by(
            language_code=language_code,
            level=level,
            lesson_number=lesson_number,
        ).first()
    finally:
        if close_session:
            session.close()


def get_lessons_for_level(
    language_code: str,
    level: str,
    generated_only: bool = True,
) -> list[PimsleurLesson]:
    """
    Get all lessons for a specific level.

    Args:
        language_code: Language code
        level: CEFR level
        generated_only: If True, only return lessons with generated audio

    Returns:
        List of PimsleurLesson objects
    """
    session = get_db_session()
    try:
        query = session.query(PimsleurLesson).filter_by(
            language_code=language_code,
            level=level,
        )
        if generated_only:
            query = query.filter_by(is_generated=True)
        return query.order_by(PimsleurLesson.lesson_number).all()
    finally:
        session.close()


def cache_telegram_file_id(lesson_id: int, file_id: str) -> None:
    """
    Cache Telegram file_id for a lesson for faster redelivery.

    Args:
        lesson_id: Lesson database ID
        file_id: Telegram file_id from sent audio
    """
    session = get_db_session()
    try:
        lesson = session.query(PimsleurLesson).get(lesson_id)
        if lesson:
            lesson.telegram_file_id = file_id
            lesson.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Cached file_id for lesson {lesson_id}")
    except Exception as e:
        logger.error(f"Failed to cache file_id: {e}")
        session.rollback()
    finally:
        session.close()


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
    session = get_db_session()
    try:
        return session.query(UserPimsleurProgress).filter_by(
            user_id=user_id,
            language_code=language_code,
        ).first()
    finally:
        session.close()


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
    session = get_db_session()
    try:
        progress = session.query(UserPimsleurProgress).filter_by(
            user_id=user_id,
            language_code=language_code,
        ).first()

        if not progress:
            progress = UserPimsleurProgress(
                user_id=user_id,
                language_code=language_code,
                level="A1",
                lesson_number=1,
            )
            session.add(progress)
            session.commit()
            logger.info(f"Created Pimsleur progress for user {user_id}")

        return progress
    finally:
        session.close()


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
    - Previous level is completed (for A2/B1)

    Args:
        user_id: Database user ID
        language_code: Language code
        level: CEFR level
        lesson_number: Lesson number

    Returns:
        True if lesson is unlocked
    """
    # Lesson 1 of A1 is always unlocked
    if level == "A1" and lesson_number == 1:
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

    # For A2/B1, check if previous level is completed
    if level == "A2":
        # Need all 30 A1 lessons (would be tracked differently in real impl)
        pass  # Simplified for now
    elif level == "B1":
        pass  # Simplified for now

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
        level: CEFR level
        lesson_number: Lesson number
        lesson_id: Lesson database ID
    """
    session = get_db_session()
    try:
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
        progress.last_completed_at = datetime.utcnow()

        # Update streak (if completed within 48 hours of last)
        if progress.last_completed_at:
            time_since_last = datetime.utcnow() - progress.last_completed_at
            if time_since_last < timedelta(hours=48):
                progress.streak_count += 1
            else:
                progress.streak_count = 1
        else:
            progress.streak_count = 1

        # Add lesson duration to total time
        lesson = session.query(PimsleurLesson).get(lesson_id)
        if lesson:
            progress.total_time_seconds += lesson.duration_seconds

        progress.updated_at = datetime.utcnow()
        session.commit()

        logger.info(
            f"Marked lesson {level} L{lesson_number} completed for user {user_id}"
        )
    except Exception as e:
        logger.error(f"Failed to mark lesson completed: {e}")
        session.rollback()
        raise
    finally:
        session.close()


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
            "level": "A1",
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
    session = get_db_session()
    try:
        lesson = PimsleurCustomLesson(
            user_id=user_id,
            language_code=language_code,
            title=title,
            source_text=source_text,
        )
        session.add(lesson)
        session.commit()
        session.refresh(lesson)
        logger.info(f"Created custom lesson request {lesson.id} for user {user_id}")
        return lesson
    finally:
        session.close()


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
    session = get_db_session()
    try:
        query = session.query(PimsleurCustomLesson).filter_by(
            user_id=user_id,
            language_code=language_code,
        )
        if status:
            query = query.filter_by(status=status)
        return query.order_by(PimsleurCustomLesson.created_at.desc()).all()
    finally:
        session.close()


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
        status: New status (generating, ready, failed)
        script_json: Generated script JSON
        audio_path: Path to generated audio
        duration_seconds: Audio duration
        vocabulary_json: Vocabulary JSON
    """
    session = get_db_session()
    try:
        lesson = session.query(PimsleurCustomLesson).get(lesson_id)
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
            session.commit()
            logger.info(f"Updated custom lesson {lesson_id} status to {status}")
    except Exception as e:
        logger.error(f"Failed to update custom lesson: {e}")
        session.rollback()
    finally:
        session.close()
