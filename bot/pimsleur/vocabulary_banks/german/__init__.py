"""
German vocabulary bank module.

Provides vocabulary data for all German units across 3 levels.
"""

from bot.pimsleur.vocabulary_banks.german.categories import (
    UNIT_THEMES,
    get_unit_theme,
    LEVEL_CEFR_MAPPING,
)

__all__ = ["UNIT_THEMES", "get_unit_theme", "LEVEL_CEFR_MAPPING"]
