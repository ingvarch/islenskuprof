"""
Vocabulary bank system with hybrid loading (curated banks + LLM fallback).

This module provides vocabulary data for all levels and units, with graceful
fallback to LLM-generated content when curated data is not available.
"""

import logging
from importlib import import_module
from typing import Optional

logger = logging.getLogger(__name__)

# Language code to module name mapping
LANGUAGE_MODULES = {
    "is": "icelandic",
    "de": "german",
}

# Module-level cache (shared across all instances, persists for process lifetime)
# Structure: {language_code: {cache_key: unit_data}}
_VOCABULARY_CACHE: dict[str, dict] = {}


def clear_vocabulary_cache(language_code: str | None = None) -> None:
    """
    Clear vocabulary cache globally or for a specific language.

    Args:
        language_code: If provided, clear only that language's cache.
                      If None, clear entire cache.
    """
    global _VOCABULARY_CACHE
    if language_code:
        _VOCABULARY_CACHE.pop(language_code, None)
    else:
        _VOCABULARY_CACHE.clear()


class VocabularyBank:
    """
    Manages vocabulary loading with LLM fallback.

    Uses module-level cache to avoid re-importing vocabulary modules
    on every request. Cache persists for the process lifetime.

    Usage:
        bank = VocabularyBank("is")  # Icelandic
        unit_data = bank.get_unit(level=1, unit=5)
    """

    def __init__(self, language_code: str = "is"):
        """
        Initialize vocabulary bank for a language.

        Args:
            language_code: ISO language code (e.g., "is" for Icelandic)
        """
        self.language_code = language_code
        # Use shared module-level cache keyed by language
        if language_code not in _VOCABULARY_CACHE:
            _VOCABULARY_CACHE[language_code] = {}
        self._cache = _VOCABULARY_CACHE[language_code]

    def get_unit(self, level: int, unit: int) -> Optional[dict]:
        """
        Get vocabulary for a specific unit.

        Tries curated bank first, falls back to LLM if missing.

        Args:
            level: Course level (1, 2, or 3)
            unit: Unit number (1-30)

        Returns:
            Dictionary with unit vocabulary data, or None if completely unavailable
        """
        cache_key = f"{level}_{unit}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try loading from bank file
        unit_data = self._load_from_bank(level, unit)

        if unit_data and unit_data.get("vocabulary"):
            logger.info(f"Loaded L{level}U{unit} from vocabulary bank")
            self._cache[cache_key] = unit_data
            return unit_data

        # Fallback to LLM generation
        logger.warning(f"No bank data for L{level}U{unit}, using LLM fallback")
        unit_data = self._generate_fallback(level, unit)
        self._cache[cache_key] = unit_data
        return unit_data

    def _load_from_bank(self, level: int, unit: int) -> Optional[dict]:
        """Load vocabulary from bank file."""
        try:
            module_name = LANGUAGE_MODULES.get(
                self.language_code, self.language_code
            )
            module_path = (
                f"bot.pimsleur.vocabulary_banks.{module_name}"
                f".level_{level:02d}.unit_{unit:02d}"
            )
            module = import_module(module_path)

            return {
                "unit": unit,
                "level": level,
                "title": module.UNIT_INFO.get("title", f"Unit {unit}"),
                "cefr": module.UNIT_INFO.get("cefr", self._default_cefr(level)),
                "categories": module.UNIT_INFO.get("categories", []),
                "opening_dialogue": getattr(module, "OPENING_DIALOGUE", []),
                "vocabulary": getattr(module, "VOCABULARY", []),
                "phrases": getattr(module, "PHRASES", []),
                "grammar_notes": getattr(module, "GRAMMAR_NOTES", []),
                "review_from_units": getattr(module, "REVIEW_FROM_UNITS", []),
                "source": "bank",
            }
        except ImportError:
            return None
        except Exception as e:
            logger.error(f"Error loading bank L{level}U{unit}: {e}")
            return None

    def _generate_fallback(self, level: int, unit: int) -> dict:
        """Generate vocabulary using LLM fallback."""
        try:
            from bot.pimsleur.vocabulary_banks.fallback_prompts import (
                generate_unit_vocabulary,
            )

            return generate_unit_vocabulary(
                language_code=self.language_code,
                level=level,
                unit=unit,
            )
        except Exception as e:
            logger.error(f"LLM fallback failed for L{level}U{unit}: {e}")
            # Return minimal placeholder
            return self._get_placeholder(level, unit)

    def _get_placeholder(self, level: int, unit: int) -> dict:
        """Get placeholder data when all else fails."""
        from bot.pimsleur.vocabulary_banks.icelandic.categories import (
            get_unit_theme,
        )

        theme, title = get_unit_theme(level, unit)
        cefr = self._default_cefr(level)

        return {
            "unit": unit,
            "level": level,
            "title": title,
            "cefr": cefr,
            "categories": [theme],
            "opening_dialogue": [],
            "vocabulary": [],
            "phrases": [],
            "grammar_notes": [],
            "review_from_units": self._get_review_units(unit),
            "source": "placeholder",
        }

    def _default_cefr(self, level: int) -> str:
        """Get default CEFR level for a course level."""
        return {1: "A1", 2: "A2", 3: "B1"}.get(level, "A1")

    def _get_review_units(self, unit: int) -> list[int]:
        """Get units to review from (spaced repetition)."""
        review_offsets = [1, 2, 5, 10]
        return [u for u in [unit - offset for offset in review_offsets] if u >= 1]

    def has_bank_data(self, level: int, unit: int) -> bool:
        """Check if curated bank data exists for a unit."""
        unit_data = self._load_from_bank(level, unit)
        return bool(unit_data and unit_data.get("vocabulary"))

    def get_bank_coverage(self) -> dict:
        """Get statistics on bank coverage vs LLM fallback."""
        coverage = {"bank": 0, "fallback": 0, "total": 90}

        for level in range(1, 4):
            for unit in range(1, 31):
                if self.has_bank_data(level, unit):
                    coverage["bank"] += 1
                else:
                    coverage["fallback"] += 1

        coverage["percent_curated"] = round(
            coverage["bank"] / coverage["total"] * 100, 1
        )
        return coverage

    def get_available_units(self, level: int) -> list[int]:
        """Get list of units with curated bank data for a level."""
        available = []
        for unit in range(1, 31):
            if self.has_bank_data(level, unit):
                available.append(unit)
        return available
