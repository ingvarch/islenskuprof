"""
German vocabulary module for Pimsleur-style lessons.
Stub module - to be populated with German vocabulary.
"""

from typing import Optional


def get_level_vocabulary(level: int) -> dict:
    """Get vocabulary dictionary for a specific level."""
    if level == 1:
        from .level_01 import VOCABULARY

        return VOCABULARY
    return {}


def get_unit(level: int, unit: int) -> Optional[dict]:
    """Get unit configuration."""
    if level == 1:
        from .level_01 import UNITS

        if 1 <= unit <= len(UNITS):
            return UNITS[unit - 1]
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
