"""
Custom exceptions for Pimsleur module.
"""


class PimsleurError(Exception):
    """Base exception for Pimsleur module."""
    pass


class LessonNotFoundError(PimsleurError):
    """Lesson does not exist or is not generated."""
    pass


class LessonLockedError(PimsleurError):
    """User has not unlocked this lesson yet."""

    def __init__(self, lesson_number: int, required_lesson: int):
        self.lesson_number = lesson_number
        self.required_lesson = required_lesson
        super().__init__(
            f"Lesson {lesson_number} is locked. "
            f"Complete lesson {required_lesson} first."
        )


class GenerationError(PimsleurError):
    """Error during lesson script generation."""
    pass


class AudioAssemblyError(PimsleurError):
    """Error during audio file assembly."""
    pass


class InvalidScriptError(PimsleurError):
    """Lesson script is malformed or invalid."""
    pass


class VocabularyError(PimsleurError):
    """Error in vocabulary processing."""
    pass
