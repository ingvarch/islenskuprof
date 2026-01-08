"""
Language registry and helpers for Pimsleur vocabulary system.
Provides unified access to vocabulary across all supported languages.
"""

from typing import Optional

# Registry of supported languages
SUPPORTED_LANGUAGES = {
    "icelandic": {
        "code": "is",
        "name": "Icelandic",
        "native_name": "Íslenska",
        "levels": [1],  # Available levels
    },
    "german": {
        "code": "de",
        "name": "German",
        "native_name": "Deutsch",
        "levels": [],  # Placeholder, no content yet
    },
}


def get_language_info(language: str) -> Optional[dict]:
    """Get language metadata."""
    return SUPPORTED_LANGUAGES.get(language.lower())


def get_vocabulary(language: str, level: int) -> dict:
    """
    Get vocabulary for a specific language and level.

    Returns dict of {category: [(word, translation, type, pronunciation), ...]}
    """
    language = language.lower()

    if language == "icelandic":
        from .icelandic import get_level_vocabulary

        return get_level_vocabulary(level)
    elif language == "german":
        from .german import get_level_vocabulary

        return get_level_vocabulary(level)

    return {}


def get_unit_config(language: str, level: int, unit: int) -> Optional[dict]:
    """
    Get configuration for a specific unit.

    Returns dict with: title, opening_dialogue, categories, new_words,
                      grammar_notes, review_from_units
    """
    language = language.lower()

    if language == "icelandic":
        from .icelandic import get_unit

        return get_unit(level, unit)
    elif language == "german":
        from .german import get_unit

        return get_unit(level, unit)

    return None


def get_vocabulary_by_category(language: str, level: int, category: str) -> list:
    """Get vocabulary items for a specific category."""
    vocab = get_vocabulary(language, level)
    return vocab.get(category, [])


def get_all_categories(language: str, level: int) -> list:
    """Get list of all categories available for a language/level."""
    vocab = get_vocabulary(language, level)
    return list(vocab.keys())


def get_bonus_packs(language: str, level: int) -> dict:
    """Get bonus pack configurations for a language/level."""
    language = language.lower()

    if language == "icelandic":
        from .icelandic import get_bonus_packs as get_is_bonus

        return get_is_bonus(level)
    elif language == "german":
        from .german import get_bonus_packs as get_de_bonus

        return get_de_bonus(level)

    return {}
