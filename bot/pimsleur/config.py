"""
Universal configuration for Pimsleur lesson generation.
Timing, voices, and settings that apply across all languages.
"""

# Lesson timing constants (in seconds)
# Based on analysis of original Pimsleur Icelandic transcripts
LESSON_DURATION_TARGET = 1800  # 30 minutes per unit
PAUSE_ANTICIPATION = 3.5  # Pause for user to formulate response
PAUSE_REPETITION = 2.5  # Pause for user to repeat (matches original ~2.1-2.8s)
PAUSE_BETWEEN_SEGMENTS = 1.2  # Small pause between segments
PAUSE_BETWEEN_WORDS = 2.2  # Pause between new word introduction

# Spaced repetition intervals (in seconds from word introduction)
# Based on Pimsleur's graduated interval recall research
SPACED_REPETITION_INTERVALS = [5, 25, 120, 600, 1200]  # 5s, 25s, 2min, 10min, 20min

# Cross-unit review: which previous units to review from
# For unit N, review vocabulary from units N-offset
CROSS_UNIT_REVIEW_OFFSETS = [1, 2, 5, 10]

# Voice configurations by language
VOICES = {
    "narrator": {
        "voice_id": "ai3-Jony",
        "language_code": "en-US",
        "description": "English narrator for instructions",
    },
    # Icelandic voices
    "native_female_is": {
        "voice_id": "ai3-is-IS-Svana",
        "language_code": "is-IS",
        "description": "Icelandic female native speaker",
    },
    "native_male_is": {
        "voice_id": "ai3-is-IS-Ulfr",
        "language_code": "is-IS",
        "description": "Icelandic male native speaker",
    },
    # German voices
    "native_female_de": {
        "voice_id": "pro1-Helena",
        "language_code": "de-DE",
        "description": "German female native speaker",
    },
    "native_male_de": {
        "voice_id": "pro1-Thomas",
        "language_code": "de-DE",
        "description": "German male native speaker",
    },
}

# Pimsleur vocabulary categories (used across all languages)
CATEGORIES = [
    "survival_skills",      # ~90 words - emergency, basic needs
    "food",                 # ~61 words - food, drinks, restaurants
    "general_phrases",      # ~37 words - common expressions
    "travel",               # ~35 words - transportation, directions
    "friends_family",       # ~33 words - people, relationships
    "money",                # ~31 words - currency, shopping
    "speak_understand",     # ~30 words - language learning phrases
    "meet_greet",           # ~25 words - greetings, introductions
    "time",                 # ~24 words - time expressions
    "shopping",             # ~20 words - stores, buying
    "numbers",              # ~18 words - counting
    "directions",           # ~14 words - navigation
]

# Bonus pack configuration
BONUS_PACK_INTERVAL = 5  # Unlock bonus pack every N units
BONUS_PACK_WORDS = 30    # Words per bonus pack
