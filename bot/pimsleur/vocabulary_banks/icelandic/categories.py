"""
Icelandic vocabulary categories and unit themes.

Based on analysis of 30 real Pimsleur Icelandic transcriptions.
Each level has 30 units with specific themes and CEFR targets.

Level 1: A1-A2 (Survival Icelandic) - 500 words
Level 2: A2-B1 (Conversational Icelandic) - 500 words
Level 3: B1-B2 (Fluent Icelandic) - 500 words
"""

# CEFR level mapping for each course level
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

# Unit themes for all 90 units
# Format: {level: {unit: (category, title)}}
UNIT_THEMES = {
    # Level 1: A1-A2 (Survival Icelandic)
    1: {
        1: ("survival_skills", "Excuse Me, Do You Understand?"),
        2: ("meet_greet", "Hello, How Are You?"),
        3: ("nationalities", "Are You Icelandic?"),
        4: ("directions_basic", "Yes, You Do Speak Icelandic!"),
        5: ("personal_info", "Where Are You From?"),
        6: ("numbers_basic", "How Many?"),
        7: ("time_basic", "What Time Is It?"),
        8: ("food_basic", "I'm Hungry"),
        9: ("drinks", "Something to Drink?"),
        10: ("restaurant", "At the Restaurant"),
        11: ("money_basic", "How Much Does It Cost?"),
        12: ("shopping_basic", "I'd Like to Buy"),
        13: ("transport", "How Do I Get There?"),
        14: ("directions_detail", "Turn Left, Turn Right"),
        15: ("family", "My Family"),
        16: ("occupations", "What Do You Do?"),
        17: ("weather", "What's the Weather Like?"),
        18: ("days_week", "What Day Is It?"),
        19: ("months_seasons", "What Month Is It?"),
        20: ("hotel", "I Have a Reservation"),
        21: ("phone", "What's Your Number?"),
        22: ("past_basic", "Yesterday"),
        23: ("future_basic", "Tomorrow"),
        24: ("likes_dislikes", "I Like / I Don't Like"),
        25: ("health_basic", "I Don't Feel Well"),
        26: ("emergency", "I Need Help"),
        27: ("review_survival", "Survival Review"),
        28: ("review_social", "Social Review"),
        29: ("review_practical", "Practical Review"),
        30: ("level_1_final", "Level 1 Final Review"),
    },
    # Level 2: A2-B1 (Conversational Icelandic)
    2: {
        1: ("directions_complex", "Finding Your Way"),
        2: ("transactions", "At the Bank"),
        3: ("opinions_basic", "I Think That..."),
        4: ("past_tense", "What Did You Do?"),
        5: ("past_continuous", "I Was Doing"),
        6: ("comparisons", "Bigger, Better, Best"),
        7: ("preferences", "I'd Rather..."),
        8: ("invitations", "Would You Like To...?"),
        9: ("suggestions", "How About...?"),
        10: ("appointments", "Making an Appointment"),
        11: ("complaints", "I Have a Problem"),
        12: ("apologies", "I'm Sorry"),
        13: ("requests_polite", "Could You Please...?"),
        14: ("obligations", "I Have To / I Must"),
        15: ("abilities", "I Can / I Know How To"),
        16: ("possibilities", "Maybe / Perhaps"),
        17: ("descriptions_people", "What Does He Look Like?"),
        18: ("descriptions_places", "What's It Like There?"),
        19: ("storytelling", "Let Me Tell You"),
        20: ("news_events", "Did You Hear?"),
        21: ("feelings", "How Do You Feel?"),
        22: ("relationships", "Friends and Partners"),
        23: ("culture_basic", "Icelandic Traditions"),
        24: ("travel_planning", "Planning a Trip"),
        25: ("accommodations", "Where to Stay"),
        26: ("activities", "Things to Do"),
        27: ("review_conversations", "Conversation Review"),
        28: ("review_past", "Past Tense Review"),
        29: ("review_opinions", "Opinions Review"),
        30: ("level_2_final", "Level 2 Final Review"),
    },
    # Level 3: B1-B2 (Fluent Icelandic)
    3: {
        1: ("hypotheticals", "If I Were..."),
        2: ("subjunctive", "I Wish That..."),
        3: ("reported_speech", "She Said That..."),
        4: ("passive_voice", "It Was Done"),
        5: ("conditionals", "If... Then..."),
        6: ("complex_past", "Had Done / Would Have"),
        7: ("formal_language", "Formal Icelandic"),
        8: ("idioms_common", "Common Expressions"),
        9: ("idioms_advanced", "Advanced Idioms"),
        10: ("proverbs", "Icelandic Proverbs"),
        11: ("abstract_nouns", "Ideas and Concepts"),
        12: ("academic_vocab", "Education and Work"),
        13: ("legal_admin", "Official Language"),
        14: ("medical_detailed", "At the Doctor"),
        15: ("technical_basic", "Technology Terms"),
        16: ("nature_geography", "Iceland's Nature"),
        17: ("history_culture", "Icelandic History"),
        18: ("literature_arts", "Books and Arts"),
        19: ("politics_society", "Society and Politics"),
        20: ("debate_argue", "Agreeing and Disagreeing"),
        21: ("nuance_tone", "Tone and Register"),
        22: ("humor_sarcasm", "Icelandic Humor"),
        23: ("regional_dialects", "Dialect Awareness"),
        24: ("old_icelandic", "Classical Icelandic"),
        25: ("modern_slang", "Modern Expressions"),
        26: ("review_advanced", "Advanced Review"),
        27: ("review_grammar", "Grammar Mastery"),
        28: ("review_idioms", "Idioms Mastery"),
        29: ("review_fluency", "Fluency Practice"),
        30: ("level_3_final", "Level 3 Final Review"),
    },
}


def get_unit_theme(level: int, unit: int) -> tuple[str, str]:
    """
    Get theme and title for a specific unit.

    Args:
        level: Course level (1, 2, or 3)
        unit: Unit number (1-30)

    Returns:
        Tuple of (category, title)
    """
    if level in UNIT_THEMES and unit in UNIT_THEMES[level]:
        return UNIT_THEMES[level][unit]

    # Default fallback
    return ("general", f"Unit {unit}")


def get_cefr_for_level(level: int) -> str:
    """Get primary CEFR level for a course level."""
    return LEVEL_CEFR_MAPPING.get(level, {}).get("primary", "A1")


def get_level_name(level: int) -> str:
    """Get human-readable name for a course level."""
    return LEVEL_CEFR_MAPPING.get(level, {}).get("name", "Beginner")


# Category descriptions for reference
CATEGORY_DESCRIPTIONS = {
    # Level 1 categories
    "survival_skills": "Emergency and basic needs vocabulary",
    "meet_greet": "Greetings, introductions, farewells",
    "nationalities": "Countries, nationalities, origins",
    "directions_basic": "Basic directions, locations",
    "personal_info": "Personal information, names, addresses",
    "numbers_basic": "Numbers 1-100, ordinals",
    "time_basic": "Hours, minutes, time expressions",
    "food_basic": "Common foods, meals",
    "drinks": "Beverages, ordering drinks",
    "restaurant": "Restaurant vocabulary, ordering food",
    "money_basic": "Currency, prices, payments",
    "shopping_basic": "Basic shopping vocabulary",
    "transport": "Transportation, getting around",
    "directions_detail": "Detailed directions, landmarks",
    "family": "Family members, relationships",
    "occupations": "Jobs, professions",
    "weather": "Weather terms, seasons",
    "days_week": "Days of the week",
    "months_seasons": "Months, seasons, dates",
    "hotel": "Hotel vocabulary, reservations",
    "phone": "Phone numbers, communication",
    "past_basic": "Simple past tense",
    "future_basic": "Simple future expressions",
    "likes_dislikes": "Preferences, opinions",
    "health_basic": "Basic health, body parts",
    "emergency": "Emergency vocabulary",
    # Level 2 categories
    "directions_complex": "Complex directions, navigation",
    "transactions": "Banking, services, official matters",
    "opinions_basic": "Expressing opinions",
    "past_tense": "Past tense verbs",
    "past_continuous": "Continuous past actions",
    "comparisons": "Comparative and superlative forms",
    "preferences": "Expressing preferences",
    "invitations": "Making and responding to invitations",
    "suggestions": "Making suggestions",
    "appointments": "Scheduling, appointments",
    "complaints": "Expressing complaints",
    "apologies": "Apologizing, excusing",
    "requests_polite": "Polite requests",
    "obligations": "Expressing obligations",
    "abilities": "Expressing abilities",
    "possibilities": "Expressing possibilities",
    "descriptions_people": "Describing people",
    "descriptions_places": "Describing places",
    "storytelling": "Narrative structures",
    "news_events": "Discussing news and events",
    "feelings": "Emotions, mental states",
    "relationships": "Personal relationships",
    "culture_basic": "Basic cultural knowledge",
    "travel_planning": "Planning trips",
    "accommodations": "Accommodation vocabulary",
    "activities": "Activities, hobbies",
    # Level 3 categories
    "hypotheticals": "Hypothetical situations",
    "subjunctive": "Subjunctive mood",
    "reported_speech": "Indirect speech",
    "passive_voice": "Passive constructions",
    "conditionals": "Conditional structures",
    "complex_past": "Complex past tenses",
    "formal_language": "Formal register",
    "idioms_common": "Common idioms",
    "idioms_advanced": "Advanced idioms",
    "proverbs": "Icelandic proverbs",
    "abstract_nouns": "Abstract concepts",
    "academic_vocab": "Academic vocabulary",
    "legal_admin": "Legal and administrative language",
    "medical_detailed": "Medical vocabulary",
    "technical_basic": "Technology terms",
    "nature_geography": "Nature and geography",
    "history_culture": "History and culture",
    "literature_arts": "Literature and arts",
    "politics_society": "Politics and society",
    "debate_argue": "Argumentation vocabulary",
    "nuance_tone": "Nuance and tone",
    "humor_sarcasm": "Humor, irony, sarcasm",
    "regional_dialects": "Dialect awareness",
    "old_icelandic": "Classical Icelandic",
    "modern_slang": "Modern slang",
}
