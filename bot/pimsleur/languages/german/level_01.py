"""
German Level 1 vocabulary and unit configurations.
Stub file - to be populated with German Pimsleur content.

Vocabulary format: (german, english, type, pronunciation)
"""

LEVEL_INFO = {
    "level": 1,
    "total_units": 30,
    "language": "german",
    "language_code": "de",
    "description": "Pimsleur German Level 1",
}

# Vocabulary organized by Pimsleur category
# Format: (german, english, word_type, pronunciation_guide)
VOCABULARY = {
    "survival_skills": [],
    "speak_understand": [],
    "meet_greet": [],
    "general_phrases": [],
    "directions": [],
    "food": [],
    "travel": [],
    "friends_family": [],
    "money": [],
    "time": [],
    "shopping": [],
    "numbers": [],
}

# Unit configurations - placeholder
UNITS = []

# Extend UNITS list to 30 with empty placeholders
while len(UNITS) < LEVEL_INFO["total_units"]:
    unit_num = len(UNITS) + 1
    UNITS.append(
        {
            "title": f"Unit {unit_num}",
            "opening_dialogue": [],
            "categories": [],
            "new_words": [],
            "grammar_notes": [],
            "review_from_units": list(range(1, unit_num)) if unit_num > 1 else [],
        }
    )

# Bonus packs - placeholder
BONUS_PACKS = {}
