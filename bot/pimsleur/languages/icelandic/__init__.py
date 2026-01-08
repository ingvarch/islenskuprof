"""
Icelandic vocabulary module for Pimsleur-style lessons.

Structure:
- level_01.py - Level 1 aggregator
- level_01_01.py - Unit 1 vocabulary and config
- level_01_02.py - Unit 2 vocabulary and config
- ...
"""

from typing import Optional


def get_level_vocabulary(level: int) -> dict:
    """Get vocabulary dictionary for a specific level, organized by category."""
    if level == 1:
        from .level_01 import VOCABULARY

        return VOCABULARY
    return {}


def get_unit(level: int, unit: int) -> Optional[dict]:
    """
    Get unit configuration.

    Returns dict with: unit, level, title, categories, opening_dialogue,
                       vocabulary, phrases, grammar_notes, review_from_units
    """
    if level == 1:
        from .level_01 import get_unit as get_level1_unit

        return get_level1_unit(unit)
    return None


def get_units_count(level: int) -> int:
    """Get total number of units in a level."""
    if level == 1:
        from .level_01 import LEVEL_INFO

        return LEVEL_INFO["total_units"]
    return 0


def get_level_info(level: int) -> Optional[dict]:
    """Get level metadata."""
    if level == 1:
        from .level_01 import LEVEL_INFO

        return LEVEL_INFO
    return None


def get_bonus_packs(level: int) -> dict:
    """Get bonus pack configurations for a level."""
    if level == 1:
        from .level_01 import BONUS_PACKS

        return BONUS_PACKS
    return {}


def get_word_pronunciation(level: int, word: str) -> Optional[str]:
    """Look up pronunciation guide for a word."""
    vocab = get_level_vocabulary(level)
    for category_words in vocab.values():
        for item in category_words:
            if item[0].lower() == word.lower():
                return item[3] if len(item) > 3 else None
    return None


def get_unit_vocabulary(level: int, unit: int) -> list:
    """Get vocabulary list for a specific unit."""
    unit_config = get_unit(level, unit)
    if unit_config:
        return unit_config.get("vocabulary", [])
    return []


def get_unit_phrases(level: int, unit: int) -> list:
    """Get phrases/expressions for a specific unit."""
    unit_config = get_unit(level, unit)
    if unit_config:
        return unit_config.get("phrases", [])
    return []


def get_available_units(level: int) -> list[int]:
    """Get list of unit numbers that have content (not placeholders)."""
    if level != 1:
        return []

    from .level_01 import get_unit as get_level1_unit

    available = []
    for i in range(1, 31):
        unit = get_level1_unit(i)
        if unit and unit.get("vocabulary"):
            available.append(i)
    return available
