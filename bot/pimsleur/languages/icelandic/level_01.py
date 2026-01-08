"""
Icelandic Level 1 - aggregates all unit files.
Based on Pimsleur Icelandic transcripts analysis.

Each unit is in its own file: level_01_01.py, level_01_02.py, etc.
"""

from importlib import import_module
from typing import Optional

LEVEL_INFO = {
    "level": 1,
    "total_units": 30,
    "language": "icelandic",
    "language_code": "is",
    "description": "Pimsleur Icelandic Level 1",
}

# Bonus packs: Unlocked after completing unit groups
BONUS_PACKS = {
    5: {
        "title": "Bonus: Survival Essentials",
        "words": 30,
        "categories": ["survival_skills", "general_phrases"],
        "description": "Essential words for getting by in Iceland",
    },
    10: {
        "title": "Bonus: Food & Drink",
        "words": 30,
        "categories": ["food"],
        "description": "Restaurant and food vocabulary",
    },
    15: {
        "title": "Bonus: Getting Around",
        "words": 30,
        "categories": ["travel", "directions"],
        "description": "Transportation and navigation",
    },
    20: {
        "title": "Bonus: Social Situations",
        "words": 30,
        "categories": ["friends_family", "meet_greet"],
        "description": "Meeting people and social interactions",
    },
    25: {
        "title": "Bonus: Shopping & Money",
        "words": 30,
        "categories": ["money", "shopping"],
        "description": "Buying things and handling money",
    },
    30: {
        "title": "Bonus: Time & Numbers",
        "words": 30,
        "categories": ["time", "numbers"],
        "description": "Telling time and counting",
    },
}


def _load_unit_module(unit_num: int):
    """Load a unit module by number."""
    try:
        module_name = f".level_01_{unit_num:02d}"
        return import_module(module_name, package="bot.pimsleur.languages.icelandic")
    except ImportError:
        return None


def get_unit(unit_num: int) -> Optional[dict]:
    """
    Get unit configuration by number.

    Returns dict with: title, opening_dialogue, categories, vocabulary,
                       phrases, grammar_notes, review_from_units
    """
    module = _load_unit_module(unit_num)
    if module is None:
        # Return placeholder for units without content yet
        return {
            "unit": unit_num,
            "level": 1,
            "title": f"Unit {unit_num}",
            "categories": [],
            "opening_dialogue": [],
            "vocabulary": [],
            "phrases": [],
            "grammar_notes": [],
            "review_from_units": list(range(1, unit_num)) if unit_num > 1 else [],
        }

    return {
        "unit": unit_num,
        "level": 1,
        "title": module.UNIT_INFO.get("title", f"Unit {unit_num}"),
        "categories": module.UNIT_INFO.get("categories", []),
        "opening_dialogue": getattr(module, "OPENING_DIALOGUE", []),
        "vocabulary": getattr(module, "VOCABULARY", []),
        "phrases": getattr(module, "PHRASES", []),
        "grammar_notes": getattr(module, "GRAMMAR_NOTES", []),
        "review_from_units": getattr(module, "REVIEW_FROM_UNITS", []),
    }


def get_all_units() -> list[dict]:
    """Get all units (populated and placeholders)."""
    return [get_unit(i) for i in range(1, LEVEL_INFO["total_units"] + 1)]


def get_vocabulary_by_category() -> dict:
    """
    Aggregate all vocabulary from all units, organized by category.

    Returns dict: {category: [(word, translation, type, pronunciation), ...]}
    """
    # Initialize categories
    categories = {
        "survival_skills": [],
        "speak_understand": [],
        "meet_greet": [],
        "general_phrases": [],
        "directions": [],
        "pronouns_basic": [],
        "verbs_basic": [],
        "adjectives_nationality": [],
        "question_words": [],
        "food": [],
        "travel": [],
        "friends_family": [],
        "money": [],
        "time": [],
        "shopping": [],
        "numbers": [],
    }

    seen_words = set()

    # Load vocabulary from each available unit
    for unit_num in range(1, LEVEL_INFO["total_units"] + 1):
        module = _load_unit_module(unit_num)
        if module is None:
            continue

        unit_categories = module.UNIT_INFO.get("categories", [])
        vocab = getattr(module, "VOCABULARY", [])

        # Add words to their primary category (first category in unit)
        primary_cat = unit_categories[0] if unit_categories else "general_phrases"

        for word_tuple in vocab:
            word = word_tuple[0]
            if word not in seen_words:
                seen_words.add(word)
                if primary_cat in categories:
                    categories[primary_cat].append(word_tuple)
                else:
                    categories["general_phrases"].append(word_tuple)

    return categories


# Build UNITS list for backwards compatibility
UNITS = get_all_units()

# Build VOCABULARY dict for backwards compatibility
VOCABULARY = get_vocabulary_by_category()
