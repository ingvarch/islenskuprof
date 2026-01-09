"""
Pimsleur lesson message formatter.

Formats lesson data for display in Telegram messages.
"""

# Language flags for dialogue display
LANGUAGE_FLAGS = {
    "is": ("\U0001f1ee\U0001f1f8", "\U0001f1ec\U0001f1e7"),  # Iceland, UK
    "de": ("\U0001f1e9\U0001f1ea", "\U0001f1ec\U0001f1e7"),  # Germany, UK
    "es": ("\U0001f1ea\U0001f1f8", "\U0001f1ec\U0001f1e7"),  # Spain, UK
    "fr": ("\U0001f1eb\U0001f1f7", "\U0001f1ec\U0001f1e7"),  # France, UK
}

# CEFR level mapping
LEVEL_TO_CEFR = {
    1: "A2",
    2: "B2",
    3: "C1",
}


def get_language_flags(lang_code: str) -> tuple[str, str]:
    """
    Get flag emojis for target and native languages.

    Args:
        lang_code: ISO language code

    Returns:
        Tuple of (target_flag, english_flag)
    """
    return LANGUAGE_FLAGS.get(lang_code, ("\U0001f4ac", "\U0001f1ec\U0001f1e7"))


def _format_theme(theme: str) -> str:
    """Convert theme slug to display format."""
    return theme.replace("_", " ").title()


def format_header_message(
    data: dict,
    level: int,
    unit: int,
    lang_code: str = "is",
) -> str:
    """
    Format header and dialogue message (Message 1).

    Args:
        data: Lesson display data from get_lesson_display_data()
        level: Pimsleur level (1, 2, 3)
        unit: Unit number
        lang_code: Language code for flags

    Returns:
        Formatted message string
    """
    cefr = LEVEL_TO_CEFR.get(level, f"L{level}")
    target_flag, english_flag = get_language_flags(lang_code)

    lines = [
        f"*Unit {unit} \u00b7 Level {level} ({cefr})*",
        f"*{data['title']}*",
        f"Theme: {_format_theme(data['theme'])}",
        "",
    ]

    # Opening dialogue
    if data.get("opening_dialogue"):
        lines.append("*OPENING DIALOGUE:*")
        lines.append("")

        for line in data["opening_dialogue"]:
            lines.append(f"{target_flag} {line['target']}")
            lines.append(f"{english_flag} {line['translation']}")
            lines.append("")

    return "\n".join(lines).strip()


def format_custom_lesson_header(data: dict, lang_code: str = "is") -> str:
    """
    Format header and dialogue message for custom lessons.

    Similar to format_header_message but without level/unit info.

    Args:
        data: Display data from custom lesson script
        lang_code: Language code for flags

    Returns:
        Formatted message string
    """
    target_flag, english_flag = get_language_flags(lang_code)

    lines = [
        f"*{data.get('title', 'Custom Lesson')}*",
        f"Theme: {_format_theme(data.get('theme', 'custom'))}",
        "",
    ]

    # Opening dialogue
    if data.get("opening_dialogue"):
        lines.append("*OPENING DIALOGUE:*")
        lines.append("")

        for line in data["opening_dialogue"]:
            lines.append(f"{target_flag} {line.get('target', '')}")
            lines.append(f"{english_flag} {line.get('translation', '')}")
            lines.append("")

    return "\n".join(lines).strip()


def format_vocabulary_message(data: dict, lang_code: str = "is") -> str:
    """
    Format vocabulary and phrases message (Message 2).

    Args:
        data: Lesson display data from get_lesson_display_data()
        lang_code: Language code

    Returns:
        Formatted message string
    """
    lines = []

    # Key vocabulary in code block
    if data.get("vocabulary"):
        lines.append("*KEY VOCABULARY:*")
        lines.append("")
        lines.append("```")

        # Group by word type if possible
        vocab_by_type = {}
        for item in data["vocabulary"]:
            word_type = item.get("word_type", "word")
            if word_type not in vocab_by_type:
                vocab_by_type[word_type] = []
            vocab_by_type[word_type].append(item)

        # Check if we should group (many proper nouns = countries, etc.)
        proper_nouns = vocab_by_type.get("proper noun", [])
        has_groupable_types = len(proper_nouns) >= 3

        if has_groupable_types:
            # Show non-proper nouns first
            for word_type, items in vocab_by_type.items():
                if word_type == "proper noun":
                    continue
                for item in items:
                    phonetic = f" [{item['phonetic']}]" if item.get("phonetic") else ""
                    lines.append(f"* {item['word']}{phonetic} - {item['translation']}")

            lines.append("```")

            # Then proper nouns as a group (separate code block)
            if proper_nouns:
                lines.append("")
                lines.append("*COUNTRIES/PLACES:*")
                lines.append("```")
                for item in proper_nouns:
                    lines.append(f"* {item['word']} - {item['translation']}")
                lines.append("```")
        else:
            # Simple list with phonetics (all items, no limit)
            for item in data["vocabulary"]:
                phonetic = f" [{item['phonetic']}]" if item.get("phonetic") else ""
                lines.append(f"* {item['word']}{phonetic} - {item['translation']}")
            lines.append("```")

    # Phrases section
    if data.get("phrases"):
        lines.append("")
        lines.append("*USEFUL PHRASES:*")
        lines.append("")
        lines.append("```")

        for phrase in data["phrases"]:
            lines.append(f"* {phrase['target']} - {phrase['translation']}")

        lines.append("```")

    return "\n".join(lines).strip()


def format_grammar_message(
    data: dict,
    duration_seconds: int,
) -> str:
    """
    Format grammar notes and metadata message (Message 3).

    Args:
        data: Lesson display data from get_lesson_display_data()
        duration_seconds: Lesson duration in seconds

    Returns:
        Formatted message string
    """
    lines = []

    # Grammar notes in code block
    if data.get("grammar_notes"):
        lines.append("*GRAMMAR NOTES:*")
        lines.append("")
        lines.append("```")

        for note in data["grammar_notes"]:
            lines.append(f"* {note}")

        lines.append("```")
        lines.append("")

    # Metadata line
    meta_parts = []

    if data.get("review_from_units"):
        units_str = ", ".join(str(u) for u in data["review_from_units"])
        meta_parts.append(f"Review: Units {units_str}")

    duration_min = duration_seconds // 60
    meta_parts.append(f"Duration: ~{duration_min} min")

    lines.append(" | ".join(meta_parts))

    return "\n".join(lines).strip()


def format_simple_vocabulary(vocabulary_json: list) -> str:
    """
    Format simple vocabulary list (fallback when no vocabulary bank exists).

    Args:
        vocabulary_json: Vocabulary list from lesson.vocabulary_json

    Returns:
        Formatted message string
    """
    if not vocabulary_json:
        return ""

    lines = ["*Vocabulary in this lesson:*", ""]

    for item in vocabulary_json[:15]:
        word = item.get("word", item.get("word_target", ""))
        translation = item.get("translation", item.get("word_native", ""))
        if word and translation:
            lines.append(f"\u2022 {word}: {translation}")

    return "\n".join(lines)
