"""
LLM prompts for generating vocabulary when bank files are missing.

These prompts ensure quality vocabulary selection by:
1. Specifying exact CEFR level requirements
2. Avoiding too simple or too complex words
3. Ensuring thematic coherence
4. Requiring pronunciation guides
"""

import json
import logging
from typing import Optional

from bot.pimsleur.config import CEFR_GUIDELINES, LEVEL_CEFR_MAPPING

logger = logging.getLogger(__name__)


VOCABULARY_GENERATION_SYSTEM_PROMPT = """You are an expert Icelandic language curriculum designer creating vocabulary lists for spaced repetition audio lessons.

Your task is to select vocabulary that is:
1. Appropriate for the specified CEFR level
2. Thematically coherent with the unit topic
3. Practically useful for learners
4. Correctly spelled with accurate translations
5. Includes phonetic pronunciation guides

## CRITICAL REQUIREMENTS

### CEFR Level Adherence
{cefr_guidelines}

### Pronunciation Guide Format
Use English-approximation phonetics that help English speakers:
- Capital letters = stressed syllable
- Use familiar English sounds where possible
- Examples:
  - "afsakid" -> "AHF-sa-kith"
  - "skilur" -> "SKI-lur"
  - "thu" -> "thoo"
  - "eg" -> "yeh"

### Icelandic-Specific Guidelines
- Include gender markers for adjectives: (m) for masculine, (f) for feminine
- Note case forms when relevant: nominative, accusative, dative, genitive
- Use standard Icelandic spelling (not dialectal)
- Include both singular and plural forms for key nouns

### Word Selection Criteria
- Prefer high-frequency words over rare synonyms
- Include verbs in both 1st person (eg) and 2nd person (thu) forms
- Balance word types: nouns, verbs, adjectives, adverbs, expressions
- Ensure words can be combined into meaningful phrases

You must output ONLY valid JSON. No markdown, no explanations."""


VOCABULARY_GENERATION_USER_PROMPT = """Generate vocabulary for an Icelandic spaced audio lesson.

## PARAMETERS
- Level: {level} / CEFR: {cefr}
- Unit: {unit} of 30
- Theme: {theme}
- Unit Title: {title}
- Target New Words: 15-20
- Review Words Needed: 8 (from units: {review_units})

## PREVIOUS UNITS' VOCABULARY (for context, DO NOT repeat)
{previous_vocab_summary}

## OUTPUT FORMAT

{{
  "unit_info": {{
    "unit": {unit},
    "level": {level},
    "cefr": "{cefr}",
    "title": "{title}",
    "categories": [/* 2-4 relevant categories */]
  }},
  "opening_dialogue": [
    ["Icelandic line", "English translation"],
    /* 4-8 lines that introduce key vocabulary naturally */
  ],
  "vocabulary": [
    ["icelandic_word", "english_translation", "word_type", "phonetic"],
    /* 15-20 new vocabulary items */
  ],
  "phrases": [
    ["Icelandic phrase", "English translation", "usage_note"],
    /* 4-6 key expressions using new vocabulary */
  ],
  "grammar_notes": [
    /* 3-5 grammar points relevant to this unit's vocabulary */
  ],
  "review_from_units": {review_units}
}}

## WORD TYPE OPTIONS
- noun, noun_plural, noun_genitive, noun_dative
- verb, verb_past, verb_participle
- adjective, adjective_feminine, adjective_neuter
- adverb, preposition, conjunction
- pronoun, question_word, interjection
- phrase, expression, greeting

## EXAMPLE VOCABULARY ENTRY
["afsakid", "excuse me", "phrase", "AHF-sa-kith"]
["skilur", "understand (you)", "verb", "SKI-lur"]
["bandariskur", "American (m)", "adjective", "BAN-da-REES-kur"]

Generate the vocabulary now. Output ONLY JSON."""


def get_cefr_for_level(level: int) -> str:
    """Get primary CEFR level for course level."""
    return LEVEL_CEFR_MAPPING.get(level, {}).get("primary", "A1")


def get_review_units(unit: int) -> list[int]:
    """Get units to review from (spaced repetition)."""
    review_offsets = [1, 2, 5, 10]
    return [u for u in [unit - offset for offset in review_offsets] if u >= 1]


def _format_cefr_guidelines(cefr: str) -> str:
    """Format CEFR guidelines for the prompt."""
    info = CEFR_GUIDELINES.get(cefr, CEFR_GUIDELINES.get("A1"))

    guidelines = f"""
CEFR Level: {cefr} - {info['description']}

Include vocabulary that has these characteristics:
{chr(10).join(f'- {c}' for c in info['characteristics'])}

AVOID vocabulary that is:
{chr(10).join(f'- {a}' for a in info['avoid'])}

Word length guidance: {info['word_length']}
Frequency guidance: {info['frequency']}
"""
    return guidelines


def _get_previous_vocab_summary(
    language_code: str,
    level: int,
    current_unit: int,
) -> str:
    """Get summary of vocabulary from previous units to avoid repetition."""
    if current_unit <= 1:
        return "This is the first unit - no previous vocabulary."

    # Estimate previous word count
    words_per_unit = 15
    total_words = (current_unit - 1) * words_per_unit

    return (
        f"Previous {current_unit - 1} units introduced approximately {total_words} words "
        f"covering basic survival, greetings, and conversation vocabulary. "
        f"Do NOT repeat these words - introduce NEW vocabulary for this theme."
    )


def _parse_vocabulary_response(response: str) -> dict:
    """Parse LLM JSON response into vocabulary dict."""
    cleaned = response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    data = json.loads(cleaned)

    # Normalize structure
    unit_info = data.get("unit_info", {})

    return {
        "unit": unit_info.get("unit", 0),
        "level": unit_info.get("level", 1),
        "title": unit_info.get("title", "Generated Unit"),
        "cefr": unit_info.get("cefr", "A1"),
        "categories": unit_info.get("categories", []),
        "opening_dialogue": [
            tuple(line) if isinstance(line, list) else line
            for line in data.get("opening_dialogue", [])
        ],
        "vocabulary": [
            tuple(word) if isinstance(word, list) else word
            for word in data.get("vocabulary", [])
        ],
        "phrases": [
            tuple(phrase) if isinstance(phrase, list) else phrase
            for phrase in data.get("phrases", [])
        ],
        "grammar_notes": data.get("grammar_notes", []),
        "review_from_units": data.get("review_from_units", []),
    }


def generate_unit_vocabulary(
    language_code: str,
    level: int,
    unit: int,
    ai_service=None,
) -> dict:
    """
    Generate vocabulary for a unit using LLM.

    Args:
        language_code: ISO code (e.g., "is")
        level: Course level (1, 2, 3)
        unit: Unit number (1-30)
        ai_service: Optional AI service instance

    Returns:
        Dictionary with unit vocabulary data
    """
    if ai_service is None:
        from bot.openrouter_service import OpenRouterService
        ai_service = OpenRouterService()

    # Get unit theme
    from bot.pimsleur.vocabulary_banks.icelandic.categories import get_unit_theme
    theme, title = get_unit_theme(level, unit)

    cefr = get_cefr_for_level(level)
    review_units = get_review_units(unit)

    # Format CEFR guidelines
    cefr_guidelines = _format_cefr_guidelines(cefr)

    # Get previous vocabulary summary
    previous_vocab = _get_previous_vocab_summary(language_code, level, unit)

    system_prompt = VOCABULARY_GENERATION_SYSTEM_PROMPT.format(
        cefr_guidelines=cefr_guidelines,
    )

    user_prompt = VOCABULARY_GENERATION_USER_PROMPT.format(
        level=level,
        cefr=cefr,
        unit=unit,
        theme=theme,
        title=title,
        review_units=review_units,
        previous_vocab_summary=previous_vocab,
    )

    try:
        response = ai_service.generate_with_custom_prompt(
            system_message=system_prompt,
            user_message=user_prompt,
            max_tokens=4000,
        )

        # Parse response
        result = _parse_vocabulary_response(response)
        result["source"] = "llm_fallback"
        result["generated_for"] = {"level": level, "unit": unit, "cefr": cefr}

        logger.info(
            f"Generated {len(result.get('vocabulary', []))} words for "
            f"L{level}U{unit} via LLM fallback"
        )

        return result

    except Exception as e:
        logger.error(f"LLM vocabulary generation failed: {e}")
        # Return minimal placeholder
        return {
            "unit": unit,
            "level": level,
            "title": title,
            "cefr": cefr,
            "categories": [theme],
            "opening_dialogue": [],
            "vocabulary": [],
            "phrases": [],
            "grammar_notes": [],
            "review_from_units": review_units,
            "source": "llm_fallback_failed",
            "error": str(e),
        }
