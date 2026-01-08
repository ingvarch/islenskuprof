"""
Vocabulary progression manager for Spaced Audio Course lessons.

Handles vocabulary selection, progression across units,
and cross-unit review scheduling.

Uses VocabularyBank with curated files and LLM fallback.
"""

import logging
from typing import Optional

from bot.pimsleur.config import CROSS_UNIT_REVIEW_OFFSETS

logger = logging.getLogger(__name__)


class VocabularyProgressionManager:
    """
    Manages vocabulary progression across Pimsleur units.

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

    def _get_language_module(self):
        """Get the language-specific vocabulary module."""
        from bot.pimsleur.vocabulary_banks import VocabularyBank
        return VocabularyBank(self.language_code)

    def get_unit_vocabulary(self, level: int, unit_number: int) -> list[dict]:
        """
        Get vocabulary list for a specific unit.

        Args:
            level: Pimsleur level (1, 2, 3)
            unit_number: Unit number (1-30)

        Returns:
            List of vocabulary dictionaries
        """
        lang_module = self._get_language_module()
        if not lang_module:
            logger.warning(f"No vocabulary module for language: {self.language_code}")
            return []

        unit = lang_module.get_unit(level, unit_number)
        if not unit or not unit.get("vocabulary"):
            logger.warning(f"No vocabulary for {self.language_code} L{level} U{unit_number}")
            return []

        return [
            {
                "word_target": word[0],
                "word_native": word[1],
                "word_type": word[2],
                "phonetic": word[3] if len(word) > 3 else "",
            }
            for word in unit["vocabulary"]
        ]

    def get_lesson_vocabulary(
        self,
        level: int,
        unit_number: int,
        previous_units_vocab: Optional[list[dict]] = None,
    ) -> dict:
        """
        Get vocabulary for a specific unit including new and review words.

        Args:
            level: Pimsleur level (1, 2, 3)
            unit_number: Unit number (1-30)
            previous_units_vocab: Optional list of vocabulary from previous units

        Returns:
            Dictionary with 'new' and 'review' vocabulary lists
        """
        # Get new vocabulary for this unit
        new_vocabulary = self.get_unit_vocabulary(level, unit_number)

        # Get review vocabulary from previous units
        review_vocabulary = self._get_review_words(
            level=level,
            unit_number=unit_number,
            review_count=8,  # Target ~8 review words
        )

        logger.info(
            f"Unit L{level} U{unit_number}: {len(new_vocabulary)} new words, "
            f"{len(review_vocabulary)} review words"
        )

        return {
            "new": new_vocabulary,
            "review": review_vocabulary,
            "total_unique": len(new_vocabulary) + len(review_vocabulary),
        }

    def _get_review_words(
        self,
        level: int,
        unit_number: int,
        review_count: int,
    ) -> list[dict]:
        """
        Select review words from previous units following spaced repetition.

        Reviews vocabulary from units N-1, N-2, N-5, N-10 (if they exist).

        Args:
            level: Pimsleur level
            unit_number: Current unit number
            review_count: Target number of review words

        Returns:
            List of review vocabulary items
        """
        if unit_number <= 1:
            return []

        review_words = []

        for offset in CROSS_UNIT_REVIEW_OFFSETS:
            review_unit = unit_number - offset
            if review_unit < 1:
                continue

            # Get vocabulary from review unit
            unit_vocab = self.get_unit_vocabulary(level, review_unit)

            # Take proportionally fewer words from older units
            take_count = max(1, review_count // len(CROSS_UNIT_REVIEW_OFFSETS))
            if offset > 5:
                take_count = max(1, take_count // 2)

            # Select evenly spaced words from the unit
            if unit_vocab:
                step = max(1, len(unit_vocab) // take_count)
                for i in range(0, len(unit_vocab), step):
                    if len(review_words) >= review_count:
                        break
                    word = unit_vocab[i]
                    if word not in review_words:
                        review_words.append(word)

            if len(review_words) >= review_count:
                break

        return review_words[:review_count]

    def get_review_unit_ids(self, unit_number: int) -> list[int]:
        """
        Get unit IDs that should be reviewed in this unit.

        Args:
            unit_number: Current unit number

        Returns:
            List of unit numbers to review from
        """
        review_units = []
        for offset in CROSS_UNIT_REVIEW_OFFSETS:
            review_unit = unit_number - offset
            if review_unit >= 1:
                review_units.append(review_unit)
        return review_units

    def get_theme_for_unit(self, level: int, unit_number: int) -> str:
        """
        Get the theme/topic for a specific unit.

        Args:
            level: Pimsleur level
            unit_number: Unit number (1-30)

        Returns:
            Theme string (first category of the unit)
        """
        lang_module = self._get_language_module()
        if not lang_module:
            return "general"

        unit = lang_module.get_unit(level, unit_number)
        if unit and unit.get("categories"):
            return unit["categories"][0]

        return "general"

    def get_unit_title(self, level: int, unit_number: int) -> str:
        """
        Get the title for a specific unit.

        Args:
            level: Pimsleur level
            unit_number: Unit number (1-30)

        Returns:
            Unit title string
        """
        lang_module = self._get_language_module()
        if not lang_module:
            return f"Level {level} Unit {unit_number}"

        unit = lang_module.get_unit(level, unit_number)
        if unit and unit.get("title"):
            return unit["title"]

        return f"Level {level} Unit {unit_number}"

    def get_opening_dialogue(self, level: int, unit_number: int) -> list[dict]:
        """
        Get opening dialogue for a specific unit.

        Args:
            level: Pimsleur level
            unit_number: Unit number (1-30)

        Returns:
            List of dialogue lines as dicts with 'target' and 'translation' keys
        """
        lang_module = self._get_language_module()
        if not lang_module:
            return []

        unit = lang_module.get_unit(level, unit_number)
        if not unit or not unit.get("opening_dialogue"):
            return []

        return [
            {"target": line[0], "translation": line[1]}
            for line in unit["opening_dialogue"]
        ]

    def get_grammar_notes(self, level: int, unit_number: int) -> list[str]:
        """
        Get grammar notes for a specific unit.

        Args:
            level: Pimsleur level
            unit_number: Unit number (1-30)

        Returns:
            List of grammar note strings
        """
        lang_module = self._get_language_module()
        if not lang_module:
            return []

        unit = lang_module.get_unit(level, unit_number)
        if unit and unit.get("grammar_notes"):
            return unit["grammar_notes"]

        return []

    def get_phrases(self, level: int, unit_number: int) -> list[dict]:
        """
        Get key phrases for a specific unit.

        Args:
            level: Pimsleur level
            unit_number: Unit number (1-30)

        Returns:
            List of phrase dicts with 'target', 'translation', 'note' keys
        """
        lang_module = self._get_language_module()
        if not lang_module:
            return []

        unit = lang_module.get_unit(level, unit_number)
        if not unit or not unit.get("phrases"):
            return []

        return [
            {
                "target": phrase[0],
                "translation": phrase[1],
                "note": phrase[2] if len(phrase) > 2 else "",
            }
            for phrase in unit["phrases"]
        ]

    def validate_vocabulary_coverage(
        self,
        level: int,
        unit_number: int,
        script_vocabulary: list[str],
    ) -> dict:
        """
        Validate that a unit script covers required vocabulary.

        Args:
            level: Pimsleur level
            unit_number: Unit number
            script_vocabulary: List of words used in the script

        Returns:
            Dictionary with validation results
        """
        expected = self.get_lesson_vocabulary(level, unit_number)
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
