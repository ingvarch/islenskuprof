"""
Vocabulary progression manager for Pimsleur lessons.

Handles vocabulary selection, progression across lessons,
and cross-lesson review scheduling.
"""

import logging
from typing import Optional

from bot.pimsleur.constants import (
    VOCABULARY_CURRICULUM,
    ICELANDIC_CORE_VOCABULARY_A1,
    CROSS_LESSON_REVIEW_OFFSETS,
)

logger = logging.getLogger(__name__)


class VocabularyProgressionManager:
    """
    Manages vocabulary progression across Pimsleur lessons.

    Ensures proper introduction of new words and review of
    previously learned vocabulary following spaced repetition.
    """

    def __init__(self, language_code: str = "is"):
        """
        Initialize vocabulary manager.

        Args:
            language_code: ISO language code (default: "is" for Icelandic)
        """
        self.language_code = language_code
        self._vocabulary_cache: dict = {}

    def get_core_vocabulary(self, level: str) -> list[dict]:
        """
        Get core vocabulary list for a specific level.

        Args:
            level: CEFR level (A1, A2, B1)

        Returns:
            List of vocabulary dictionaries
        """
        if self.language_code == "is" and level == "A1":
            return [
                {
                    "word_target": word[0],
                    "word_native": word[1],
                    "word_type": word[2],
                    "phonetic": word[3],
                }
                for word in ICELANDIC_CORE_VOCABULARY_A1
            ]

        # For other levels/languages, return empty (to be populated from DB or generated)
        logger.warning(f"No core vocabulary defined for {self.language_code} {level}")
        return []

    def get_lesson_vocabulary(
        self,
        level: str,
        lesson_number: int,
        previous_lessons_vocab: Optional[list[dict]] = None,
    ) -> dict:
        """
        Get vocabulary for a specific lesson including new and review words.

        Args:
            level: CEFR level
            lesson_number: Lesson number (1-30)
            previous_lessons_vocab: Optional list of vocabulary from previous lessons

        Returns:
            Dictionary with 'new' and 'review' vocabulary lists
        """
        curriculum = VOCABULARY_CURRICULUM.get(level, VOCABULARY_CURRICULUM["A1"])
        new_words_count = curriculum["new_words_per_lesson"]
        review_words_count = curriculum["review_words_per_lesson"]

        # Get core vocabulary for this level
        core_vocab = self.get_core_vocabulary(level)

        # Calculate which words to introduce in this lesson
        start_index = (lesson_number - 1) * new_words_count
        end_index = min(start_index + new_words_count, len(core_vocab))

        new_vocabulary = core_vocab[start_index:end_index] if start_index < len(core_vocab) else []

        # Get review vocabulary from previous lessons
        review_vocabulary = self._get_review_words(
            level=level,
            lesson_number=lesson_number,
            core_vocab=core_vocab,
            new_words_count=new_words_count,
            review_count=review_words_count,
        )

        logger.info(
            f"Lesson {level} L{lesson_number}: {len(new_vocabulary)} new words, "
            f"{len(review_vocabulary)} review words"
        )

        return {
            "new": new_vocabulary,
            "review": review_vocabulary,
            "total_unique": len(new_vocabulary) + len(review_vocabulary),
        }

    def _get_review_words(
        self,
        level: str,
        lesson_number: int,
        core_vocab: list[dict],
        new_words_count: int,
        review_count: int,
    ) -> list[dict]:
        """
        Select review words from previous lessons following spaced repetition.

        Reviews vocabulary from lessons N-1, N-2, N-5, N-10 (if they exist).

        Args:
            level: CEFR level
            lesson_number: Current lesson number
            core_vocab: Full vocabulary list
            new_words_count: Words per lesson
            review_count: Target number of review words

        Returns:
            List of review vocabulary items
        """
        if lesson_number <= 1:
            return []

        review_words = []

        for offset in CROSS_LESSON_REVIEW_OFFSETS:
            review_lesson = lesson_number - offset
            if review_lesson < 1:
                continue

            # Calculate which words were introduced in the review lesson
            start_idx = (review_lesson - 1) * new_words_count
            end_idx = min(start_idx + new_words_count, len(core_vocab))

            # Take a few words from each review lesson
            words_from_lesson = core_vocab[start_idx:end_idx]

            # Take proportionally fewer words from older lessons
            take_count = max(1, review_count // len(CROSS_LESSON_REVIEW_OFFSETS))
            if offset > 5:
                take_count = max(1, take_count // 2)  # Even fewer from very old lessons

            # Select evenly spaced words from the lesson
            step = max(1, len(words_from_lesson) // take_count)
            for i in range(0, len(words_from_lesson), step):
                if len(review_words) >= review_count:
                    break
                word = words_from_lesson[i]
                if word not in review_words:
                    review_words.append(word)

            if len(review_words) >= review_count:
                break

        return review_words[:review_count]

    def get_review_lesson_ids(self, lesson_number: int) -> list[int]:
        """
        Get lesson IDs that should be reviewed in this lesson.

        Args:
            lesson_number: Current lesson number

        Returns:
            List of lesson numbers to review from
        """
        review_lessons = []
        for offset in CROSS_LESSON_REVIEW_OFFSETS:
            review_lesson = lesson_number - offset
            if review_lesson >= 1:
                review_lessons.append(review_lesson)
        return review_lessons

    def get_theme_for_lesson(self, level: str, lesson_number: int) -> str:
        """
        Get the theme/topic for a specific lesson.

        Args:
            level: CEFR level
            lesson_number: Lesson number (1-30)

        Returns:
            Theme string
        """
        curriculum = VOCABULARY_CURRICULUM.get(level, VOCABULARY_CURRICULUM["A1"])
        themes = curriculum.get("themes", [])

        if lesson_number <= len(themes):
            return themes[lesson_number - 1]

        return f"review_and_practice_{lesson_number}"

    def extract_vocabulary_from_text(
        self,
        text: str,
        target_count: int = 20,
    ) -> list[dict]:
        """
        Extract vocabulary items from user-provided text.

        This is a placeholder - actual implementation would use
        NLP or LLM to extract and translate vocabulary.

        Args:
            text: Source text in target language
            target_count: Target number of vocabulary items

        Returns:
            List of vocabulary dictionaries
        """
        # Split text into words and take unique ones
        words = text.split()
        unique_words = list(dict.fromkeys(words))  # Preserve order, remove duplicates

        # Filter out very short words and punctuation
        filtered_words = [
            w.strip(".,!?;:\"'()[]") for w in unique_words
            if len(w.strip(".,!?;:\"'()[]")) > 2
        ]

        # Take top N words
        selected_words = filtered_words[:target_count]

        # Return as vocabulary items (translations would need LLM)
        return [
            {
                "word_target": word,
                "word_native": f"[translation needed: {word}]",
                "word_type": "unknown",
                "phonetic": "",
            }
            for word in selected_words
        ]

    def validate_vocabulary_coverage(
        self,
        level: str,
        lesson_number: int,
        script_vocabulary: list[str],
    ) -> dict:
        """
        Validate that a lesson script covers required vocabulary.

        Args:
            level: CEFR level
            lesson_number: Lesson number
            script_vocabulary: List of words used in the script

        Returns:
            Dictionary with validation results
        """
        expected = self.get_lesson_vocabulary(level, lesson_number)
        expected_words = {v["word_target"] for v in expected["new"]}
        expected_words.update(v["word_target"] for v in expected["review"])

        script_words = set(script_vocabulary)

        missing = expected_words - script_words
        extra = script_words - expected_words

        return {
            "valid": len(missing) == 0,
            "missing_words": list(missing),
            "extra_words": list(extra),
            "coverage_percent": (
                (len(expected_words) - len(missing)) / len(expected_words) * 100
                if expected_words else 100
            ),
        }
