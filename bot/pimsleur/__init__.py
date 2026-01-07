"""
Pimsleur Method module for generating and managing audio lessons.

This module implements the Pimsleur language learning method with:
- Spaced repetition (graduated interval recall)
- Anticipation principle (prompt -> pause -> answer)
- Core vocabulary progression
- 30-minute audio lesson format
"""

# Lazy imports to avoid circular dependencies
def get_lesson_generator():
    """Get PimsleurLessonGenerator class."""
    from bot.pimsleur.generator import PimsleurLessonGenerator
    return PimsleurLessonGenerator


def get_audio_assembler():
    """Get PimsleurAudioAssembler class."""
    from bot.pimsleur.audio_assembler import PimsleurAudioAssembler
    return PimsleurAudioAssembler


def get_vocabulary_manager():
    """Get VocabularyProgressionManager class."""
    from bot.pimsleur.vocabulary_manager import VocabularyProgressionManager
    return VocabularyProgressionManager


# Export error classes directly (no dependencies)
from bot.pimsleur.error_handling import (
    PimsleurError,
    LessonNotFoundError,
    LessonLockedError,
    GenerationError,
    AudioAssemblyError,
    InvalidScriptError,
    VocabularyError,
)

__all__ = [
    "get_lesson_generator",
    "get_audio_assembler",
    "get_vocabulary_manager",
    "PimsleurError",
    "LessonNotFoundError",
    "LessonLockedError",
    "GenerationError",
    "AudioAssemblyError",
    "InvalidScriptError",
    "VocabularyError",
]
