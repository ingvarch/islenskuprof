"""
Universal configuration for Pimsleur lesson generation.
Timing, voices, and settings that apply across all languages.
"""

# Lesson timing constants (in seconds)
# Based on analysis of original Pimsleur Icelandic transcripts
LESSON_DURATION_TARGET = 1800  # 30 minutes per unit
CUSTOM_LESSON_DURATION_TARGET = 1200  # 20 minutes for custom lessons

# Pause durations by cognitive load (based on real Pimsleur analysis)
# These variable pauses are critical - fixed pauses break the learning flow
PAUSE_SYLLABLE = 2.0  # After syllable in backward build-up (2.0-2.2s)
PAUSE_LEARNING = 2.2  # After native speaker models word (2.0-2.5s)
PAUSE_REPETITION = 2.5  # For user to repeat after model (2.2-2.8s)
PAUSE_THINKING = 3.5  # After "How do you say X?" (3.0-4.0s)
PAUSE_COMPOSITION = 4.5  # When creating new sentences (4.0-5.0s)
PAUSE_CONFIRMATION = 2.0  # Brief pause after providing answer
PAUSE_TRANSITION = 1.0  # Between major segments (0.8-1.2s)
PAUSE_DIALOGUE = 1.5  # Between dialogue lines

# Legacy aliases for backward compatibility
PAUSE_ANTICIPATION = PAUSE_THINKING
PAUSE_BETWEEN_SEGMENTS = PAUSE_TRANSITION
PAUSE_BETWEEN_WORDS = PAUSE_LEARNING

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

# Segment types for Pimsleur lessons
# Based on analysis of 9 real Pimsleur Icelandic transcriptions
SEGMENT_TYPES = {
    # Opening structure (0-60 seconds)
    "opening_title",        # "This is Unit X of Pimsleur's Icelandic"
    "opening_instruction",  # "Listen to this Icelandic conversation"
    "opening_dialogue",     # Full native dialogue at natural speed

    # Core teaching segments
    "instruction",          # Narrator guidance and context
    "native_model",         # Native speaker demonstrates word/phrase
    "syllable_practice",    # Individual syllable in backward build-up
    "repeat_after",         # "Listen and repeat"

    # Practice and recall segments
    "comprehension_question",   # "How do you say X in Icelandic?"
    "prompt_for_composition",   # "Try to say X and Y together"
    "prompt_for_question",      # "Ask her if..."
    "model_answer",             # Correct answer from native speaker
    "context_application",      # Word used in phrase/sentence

    # Review and reinforcement
    "review_in_context",    # Previous vocabulary in new context
    "dialogue_segment",     # Practice dialogue line
    "grammar_explanation",  # Brief grammar note from narrator
    "cultural_note",        # Cultural context

    # Closing structure (last 25-30 seconds)
    "closing_summary",      # "This is the end of Unit X"
    "closing_instructions", # "Continue with Unit X+1 tomorrow"

    # Utility
    "pause",                # Silent pause for user response
}

# Segment type to speaker mapping (default speakers)
SEGMENT_SPEAKER_DEFAULTS = {
    "opening_title": "narrator",
    "opening_instruction": "narrator",
    "instruction": "narrator",
    "repeat_after": "narrator",
    "comprehension_question": "narrator",
    "prompt_for_composition": "narrator",
    "prompt_for_question": "narrator",
    "grammar_explanation": "narrator",
    "cultural_note": "narrator",
    "closing_summary": "narrator",
    "closing_instructions": "narrator",
    # Native speaker segments use language-specific voices
    "native_model": "native_female",
    "syllable_practice": "native_female",
    "model_answer": "native_female",
    "context_application": "native_female",
    "review_in_context": "native_female",
    "dialogue_segment": "native_female",  # Can be male or female
}

# Lesson structure timing (approximate allocation in seconds)
LESSON_STRUCTURE = {
    "opening": 60,           # Title, instruction, dialogue
    "new_material": 660,     # 11 minutes - new vocabulary with build-up
    "spaced_practice": 960,  # 16 minutes - spaced repetition and context
    "closing": 30,           # Summary and next steps
}
