"""
Universal configuration for Spaced Audio Course lesson generation.
Timing, voices, and settings that apply across all languages.

Note: We use "Spaced Audio Course" instead of trademark names.
"""

# Lesson timing constants (in seconds)
# Based on analysis of original Pimsleur Icelandic transcripts
LESSON_DURATION_TARGET = 1800  # 30 minutes per unit
CUSTOM_LESSON_DURATION_TARGET = 1200  # 20 minutes for custom lessons

# Pause durations by cognitive load (based on analysis of 20 real Pimsleur units)
# These variable pauses are critical - fixed pauses break the learning flow
PAUSE_SYLLABLE = 2.0  # After syllable in backward build-up (2.0-2.2s)
PAUSE_LEARNING = 2.2  # After native speaker models word (2.0-2.5s)
PAUSE_REPETITION = 2.5  # For user to repeat after model (2.2-2.8s)
PAUSE_THINKING = 3.5  # After "How do you say X?" (3.0-4.0s)
PAUSE_RECALL = 3.4  # After "Do you remember how to say..." (3.4-4.0s)
PAUSE_COMPOSITION = 4.5  # When creating new sentences (4.0-5.0s)
PAUSE_CONFIRMATION = 2.0  # Brief pause after providing answer
PAUSE_TRANSITION = 1.0  # Between major segments (0.8-1.2s)
PAUSE_DIALOGUE = 1.5  # Between dialogue lines
PAUSE_REFLECTION = 6.5  # Long reflection pause in later units (6.5-8.7s)

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
    "survival_skills",  # ~90 words - emergency, basic needs
    "food",  # ~61 words - food, drinks, restaurants
    "general_phrases",  # ~37 words - common expressions
    "travel",  # ~35 words - transportation, directions
    "friends_family",  # ~33 words - people, relationships
    "money",  # ~31 words - currency, shopping
    "speak_understand",  # ~30 words - language learning phrases
    "meet_greet",  # ~25 words - greetings, introductions
    "time",  # ~24 words - time expressions
    "shopping",  # ~20 words - stores, buying
    "numbers",  # ~18 words - counting
    "directions",  # ~14 words - navigation
]

# Bonus pack configuration
BONUS_PACK_INTERVAL = 5  # Unlock bonus pack every N units
BONUS_PACK_WORDS = 30  # Words per bonus pack

# Segment types for Pimsleur lessons
# Based on analysis of 20 real Pimsleur Icelandic transcriptions
SEGMENT_TYPES = {
    # Opening structure (0-60 seconds)
    "opening_title",  # "This is Unit X of Pimsleur's Icelandic"
    "opening_instruction",  # "Listen to this Icelandic conversation"
    "opening_context",  # Context before dialogue (Unit 15+): "John has gone to..."
    "opening_preview",  # Preview phrase: "You will hear X which means Y"
    "opening_dialogue",  # Full native dialogue at natural speed
    # Core teaching segments
    "instruction",  # Narrator guidance and context
    "native_instruction",  # Instruction in target language (Unit 11+): "Hlustaðu"
    "native_model",  # Native speaker demonstrates word/phrase
    "syllable_practice",  # Individual syllable in backward build-up
    "repeat_after",  # "Listen and repeat" / "Hlustaðu og endurtaktu"
    # Practice and recall segments
    "comprehension_question",  # "How do you say X in Icelandic?"
    "recall_question",  # "Do you remember how to say..." (review from prev units)
    "prompt_for_composition",  # "Try to say X and Y together"
    "prompt_for_question",  # "Ask her if..." / "Spurðu"
    "scenario_setup",  # "Suppose you're hosting a party..."
    "model_answer",  # Correct answer from native speaker
    "context_application",  # Word used in phrase/sentence
    # Grammar teaching (discovered in Units 11-20)
    "gender_explanation",  # "Beer is a masculine word. Here's how to say..."
    "grammar_drill",  # Gender/conjugation variation drilling
    "grammar_explanation",  # Brief grammar note from narrator
    # Review and reinforcement
    "review_in_context",  # Previous vocabulary in new context
    "dialogue_segment",  # Practice dialogue line
    "cultural_note",  # Cultural context
    # Closing structure (last 25-30 seconds)
    "closing_summary",  # "This is the end of Unit X"
    "closing_instructions",  # "Continue with Unit X+1 tomorrow"
    # Utility
    "pause",  # Silent pause for user response
}

# Native language instruction phrases (for Units 11+)
# These replace English instructions in later units
NATIVE_INSTRUCTIONS = {
    "is": {
        "listen": "Hlustaðu",
        "listen_repeat": "Hlustaðu og endurtaktu",
        "listen_conversation": "Hlustaðu á þetta samtal",
        "ask": "Spurðu",
        "say": "Segðu",
        "answer_questions": "Svaraðu spurningum",
        "listen_once_more": "Hlustaðu einu sinni enn",
        "now_say": "Segðu núna",
    },
    "de": {
        "listen": "Hören Sie",
        "listen_repeat": "Hören Sie und wiederholen Sie",
        "listen_conversation": "Hören Sie dieses Gespräch",
        "ask": "Fragen Sie",
        "say": "Sagen Sie",
        "answer_questions": "Beantworten Sie die Fragen",
        "listen_once_more": "Hören Sie noch einmal",
        "now_say": "Sagen Sie jetzt",
    },
}

# Unit ranges for instruction language evolution
# Units 1-5: All English instructions
# Units 6-10: Mixed (some native commands)
# Units 11+: Primarily native language instructions
NATIVE_INSTRUCTION_START_UNIT = 6
NATIVE_INSTRUCTION_FULL_UNIT = 11

# Segment type to speaker mapping (default speakers)
SEGMENT_SPEAKER_DEFAULTS = {
    # Narrator segments (English)
    "opening_title": "narrator",
    "opening_instruction": "narrator",
    "opening_context": "narrator",
    "opening_preview": "narrator",
    "instruction": "narrator",
    "repeat_after": "narrator",
    "comprehension_question": "narrator",
    "recall_question": "narrator",
    "prompt_for_composition": "narrator",
    "prompt_for_question": "narrator",
    "scenario_setup": "narrator",
    "gender_explanation": "narrator",
    "grammar_explanation": "narrator",
    "cultural_note": "narrator",
    "closing_summary": "narrator",
    "closing_instructions": "narrator",
    # Native speaker segments (target language)
    "native_instruction": "native_female",  # Instructions in target language
    "native_model": "native_female",
    "syllable_practice": "native_female",
    "model_answer": "native_female",
    "context_application": "native_female",
    "grammar_drill": "native_female",
    "review_in_context": "native_female",
    "dialogue_segment": "native_female",  # Can be male or female
}

# Lesson structure timing (approximate allocation in seconds)
LESSON_STRUCTURE = {
    "opening": 60,  # Title, instruction, dialogue
    "new_material": 660,  # 11 minutes - new vocabulary with build-up
    "spaced_practice": 960,  # 16 minutes - spaced repetition and context
    "closing": 30,  # Summary and next steps
}

# Brand configuration (avoid trademark issues)
COURSE_BRAND_NAME = "Spaced Audio Course"
OPENING_TITLE_FORMAT = "This is Level {level}, Unit {unit} of your {language} {brand}."
CUSTOM_OPENING_TITLE_FORMAT = (
    "This is a personalized lesson. "
    "Based on provided words, difficulty level: {difficulty}."
)
CLOSING_SUMMARY_FORMAT = "This is the end of Level {level}, Unit {unit}."

# CEFR level mapping for each course level
# Level 1: Beginner (A1-A2) - 500 words
# Level 2: Intermediate (A2-B1) - 500 words
# Level 3: Upper Intermediate (B1-B2) - 500 words
LEVEL_CEFR_MAPPING = {
    1: {"primary": "A1", "secondary": "A2", "name": "Beginner", "word_target": 500},
    2: {"primary": "A2", "secondary": "B1", "name": "Intermediate", "word_target": 500},
    3: {
        "primary": "B1",
        "secondary": "B2",
        "name": "Upper Intermediate",
        "word_target": 500,
    },
}

# Progressive speech speed configuration per level
# Uses hybrid approach: TTS-native speed for small adjustments,
# RubberBand post-processing for larger speedups (better quality)
#
# speech_speed: VoiceMaker API speed parameter (-100 to 100, 0 = normal)
# pause_multiplier: Multiplier for pause durations (1.0 = full, 0.85 = 15% shorter)
# use_rubberband: Whether to use PyRubberBand for time-stretching
# stretch_rate: Time-stretch factor when using RubberBand (1.2 = 20% faster)
LEVEL_SPEED_CONFIG = {
    1: {
        "speech_speed": 0,
        "pause_multiplier": 1.0,
        "use_rubberband": False,
        "stretch_rate": 1.0,
    },
    2: {
        "speech_speed": 10,
        "pause_multiplier": 0.9,
        "use_rubberband": False,
        "stretch_rate": 1.0,
    },
    3: {
        "speech_speed": 0,
        "pause_multiplier": 0.85,
        "use_rubberband": True,
        "stretch_rate": 1.2,
    },
}

# Default speed config (fallback for unknown levels)
DEFAULT_SPEED_CONFIG = {
    "speech_speed": 0,
    "pause_multiplier": 1.0,
    "use_rubberband": False,
    "stretch_rate": 1.0,
}

# CEFR vocabulary guidelines for LLM generation
CEFR_GUIDELINES = {
    "A1": {
        "description": "Basic survival vocabulary",
        "characteristics": [
            "Concrete, tangible nouns (food, objects, places)",
            "Basic verbs (to be, to have, to want, to go)",
            "Simple adjectives (good, bad, big, small)",
            "Numbers 1-100",
            "Basic greetings and farewells",
            "Simple question words (what, where, who)",
        ],
        "avoid": [
            "Abstract concepts",
            "Complex verb tenses",
            "Idiomatic expressions",
            "Technical vocabulary",
            "Rare or literary words",
        ],
        "word_length": "Prefer shorter words (1-3 syllables)",
        "frequency": "Top 1000 most common words",
    },
    "A2": {
        "description": "Elementary conversation vocabulary",
        "characteristics": [
            "Past tense markers and common irregular verbs",
            "Comparative and superlative adjectives",
            "Prepositions of time and place",
            "Connectors (because, but, so, then)",
            "Daily routine vocabulary",
            "Simple opinions (I think, I like)",
        ],
        "avoid": [
            "Subjunctive mood",
            "Complex conditionals",
            "Specialized terminology",
            "Archaic or formal register",
        ],
        "word_length": "1-4 syllables",
        "frequency": "Top 2000 most common words",
    },
    "B1": {
        "description": "Intermediate conversational fluency",
        "characteristics": [
            "Conditional structures (if... then...)",
            "Modal verbs (could, should, might)",
            "Abstract nouns (idea, situation, experience)",
            "Common idioms and expressions",
            "Opinion and argument vocabulary",
            "Feelings and emotions vocabulary",
        ],
        "avoid": [
            "Highly specialized jargon",
            "Obscure idioms",
            "Regional dialects",
            "Literary or archaic forms",
        ],
        "word_length": "1-5 syllables",
        "frequency": "Top 3500 most common words",
    },
    "B2": {
        "description": "Upper intermediate fluency",
        "characteristics": [
            "Hypothetical and counterfactual language",
            "Nuanced vocabulary (subtle, considerable, somewhat)",
            "Formal vs informal register awareness",
            "Idiomatic expressions",
            "Academic and professional vocabulary",
            "Cultural references",
        ],
        "avoid": [
            "Highly technical terms without context",
            "Very rare vocabulary",
            "Regional slang that non-natives won't hear",
        ],
        "word_length": "Variable",
        "frequency": "Top 5000 most common words",
    },
}
