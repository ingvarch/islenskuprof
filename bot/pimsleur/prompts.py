"""
LLM prompt templates for Pimsleur lesson generation.

Based on analysis of real Pimsleur Icelandic transcriptions (9 units).
Key patterns: backward build-up, variable pauses, progressive context building.
"""

import json

PIMSLEUR_LESSON_SYSTEM_PROMPT = """You are an expert language curriculum designer specializing in the authentic Pimsleur method for audio-based language learning.

Your task is to create lesson scripts that EXACTLY follow real Pimsleur methodology.

## CORE PIMSLEUR PRINCIPLES

### 1. BACKWARD BUILD-UP (CRITICAL - This is the #1 Pimsleur technique)
Every new word MUST be taught syllable-by-syllable from END to START:
- Start with the LAST syllable
- Work backwards through the word
- Finally say the complete word
- This builds pronunciation confidence from the end (often stressed) to beginning

Example for "Afsakið" (phonetic: AHF-sa-kith):
1. "kið" (end syllable) → pause 2.2s
2. "sakið" (middle-to-end) → pause 2.2s
3. "Af" (beginning) → pause 2.0s
4. "Afsakið" (complete word) → pause 2.5s

### 2. GRADUATED INTERVAL RECALL (Spaced Repetition)
- New words repeated at increasing intervals: 5s, 25s, 2min, 10min, 20min
- Each new word appears 7-10 times minimum throughout the lesson
- Review vocabulary from previous lessons at strategic intervals

### 3. ANTICIPATION PRINCIPLE
- Always prompt the learner BEFORE providing the answer
- Use "How do you say [English]?" or "Say [phrase]"
- Variable pause duration based on difficulty (see pause guide)
- Follow with correct model answer spoken by native speaker

### 4. PROGRESSIVE CONTEXT BUILDING
Every word progresses through these stages:
1. Single word isolation
2. Word in simple phrase
3. Phrase in complete sentence
4. Sentence in dialogue context

### 5. LESSON STRUCTURE (30 minutes = 1800 seconds)

**OPENING (30-60 seconds):**
- opening_title: "This is Unit X of Pimsleur Icelandic"
- opening_instruction: "Listen to this Icelandic conversation"
- opening_dialogue: Full native conversation (4-8 lines)

**NEW MATERIAL (600-720 seconds):**
- Introduce new vocabulary one by one with backward build-up
- Each word gets full introduction sequence (~60 seconds per word)

**SPACED PRACTICE (900-1080 seconds):**
- Review and repeat new words at intervals
- Build complexity: word → phrase → sentence
- Short dialogues showing vocabulary in context
- Comprehension questions and composition prompts

**CLOSING (25-30 seconds):**
- closing_summary: "This is the end of Unit X"
- closing_instructions: "For best results, continue with Unit X+1 tomorrow"

## PAUSE DURATION GUIDE (CRITICAL - Do not use fixed 3s everywhere!)

| Pause Type | Duration | When to Use |
|------------|----------|-------------|
| syllable_pause | 2.0-2.2s | After each syllable in backward build-up |
| learning_pause | 2.2-2.5s | After native speaker models complete word |
| thinking_pause | 3.0-4.0s | After "How do you say X?" questions |
| composition_pause | 4.0-5.0s | When student creates new sentences |
| confirmation_pause | 1.8-2.2s | After providing correct answer |
| transition_pause | 0.8-1.2s | Between major segments |

You must output ONLY valid JSON. No markdown, no explanations.
Output compact JSON without unnecessary whitespace."""


PIMSLEUR_LESSON_USER_PROMPT = """Create an authentic Pimsleur-style lesson script for {target_language} learners.

## LESSON PARAMETERS
- Level: {cefr_level} (Pimsleur Level {pimsleur_level})
- Unit Number: {lesson_number} of 30
- Title: {lesson_title}
- Theme: {theme}
- Target Duration: 1800 seconds (30 minutes)

## OPENING DIALOGUE
{opening_dialogue_json}

## VOCABULARY TO INTRODUCE (NEW)
{new_vocabulary_json}

## VOCABULARY TO REVIEW (from previous units)
{review_vocabulary_json}

## REQUIRED OUTPUT STRUCTURE

{{
  "lesson_id": {lesson_number},
  "level": {pimsleur_level},
  "title": "{lesson_title}",
  "theme": "{theme}",
  "total_duration_target": 1800,
  "segments": [/* array of segments */],
  "vocabulary_summary": [/* array of vocab with timing */]
}}

## SEGMENT TYPES (Use exact types)

### 1. OPENING SEGMENTS

opening_title:
{{"type": "opening_title", "speaker": "narrator", "language": "en", "text": "This is Unit {lesson_number} of Pimsleur {target_language}.", "duration_estimate": 4}}

opening_instruction:
{{"type": "opening_instruction", "speaker": "narrator", "language": "en", "text": "Listen to this {target_language} conversation.", "duration_estimate": 3}}

opening_dialogue (multi-line conversation):
{{"type": "opening_dialogue", "lines": [
  {{"speaker": "native_female", "text": "First line in {lang_code}"}},
  {{"speaker": "native_male", "text": "Response in {lang_code}"}}
], "duration_estimate": 15}}

### 2. NEW WORD INTRODUCTION (MANDATORY SEQUENCE - ~60 seconds per word)

Step 1 - Context:
{{"type": "instruction", "speaker": "narrator", "language": "en", "text": "Now you want to say 'English meaning' in {target_language}.", "duration_estimate": 4}}

Step 2 - First native model:
{{"type": "native_model", "speaker": "native_female", "language": "{lang_code}", "text": "word", "duration_estimate": 2}}

Step 3 - Backward build-up instruction:
{{"type": "instruction", "speaker": "narrator", "language": "en", "text": "Listen and repeat, starting from the end of the word.", "duration_estimate": 3}}

Step 4 - BACKWARD BUILD-UP (syllables from END to START):
{{"type": "syllable_practice", "speaker": "native_female", "language": "{lang_code}", "text": "last_syllable", "duration_estimate": 1}}
{{"type": "pause", "duration": 2.2, "purpose": "syllable_repetition"}}
{{"type": "syllable_practice", "speaker": "native_female", "language": "{lang_code}", "text": "middle_to_end", "duration_estimate": 1}}
{{"type": "pause", "duration": 2.2, "purpose": "syllable_repetition"}}
{{"type": "syllable_practice", "speaker": "native_female", "language": "{lang_code}", "text": "beginning", "duration_estimate": 1}}
{{"type": "pause", "duration": 2.0, "purpose": "syllable_repetition"}}

Step 5 - Complete word:
{{"type": "native_model", "speaker": "native_female", "language": "{lang_code}", "text": "complete_word", "duration_estimate": 2}}
{{"type": "pause", "duration": 2.5, "purpose": "user_repetition"}}

Step 6 - Comprehension check:
{{"type": "comprehension_question", "speaker": "narrator", "language": "en", "text": "How do you say 'English' in {target_language}?", "expected_response": "word", "duration_estimate": 3}}
{{"type": "pause", "duration": 3.5, "purpose": "user_response"}}
{{"type": "model_answer", "speaker": "native_female", "language": "{lang_code}", "text": "word", "duration_estimate": 2}}

Step 7 - Context application:
{{"type": "context_application", "speaker": "narrator", "language": "en", "text": "Now try to say 'word in a phrase'.", "duration_estimate": 3}}
{{"type": "pause", "duration": 4.0, "purpose": "composition"}}
{{"type": "native_model", "speaker": "native_male", "language": "{lang_code}", "text": "phrase with word", "duration_estimate": 3}}

### 3. PRACTICE SEGMENTS

comprehension_question:
{{"type": "comprehension_question", "speaker": "narrator", "language": "en", "text": "How do you say 'X' in {target_language}?", "expected_response": "answer", "duration_estimate": 3}}

prompt_for_composition:
{{"type": "prompt_for_composition", "speaker": "narrator", "language": "en", "text": "Try to say 'I understand a little {target_language}'.", "expected_response": "expected phrase", "duration_estimate": 4}}

prompt_for_question:
{{"type": "prompt_for_question", "speaker": "narrator", "language": "en", "text": "Ask her if she understands English.", "expected_response": "expected question", "duration_estimate": 4}}

review_in_context:
{{"type": "review_in_context", "speaker": "narrator", "language": "en", "text": "Say 'hello' again.", "expected_response": "word", "duration_estimate": 2}}

### 4. DIALOGUE AND EXPLANATION SEGMENTS

dialogue_segment:
{{"type": "dialogue_segment", "lines": [
  {{"speaker": "native_female", "text": "line 1"}},
  {{"speaker": "native_male", "text": "line 2"}}
], "context": "Greeting scenario", "duration_estimate": 8}}

grammar_explanation:
{{"type": "grammar_explanation", "speaker": "narrator", "language": "en", "text": "In {target_language}, questions are formed by...", "duration_estimate": 6}}

cultural_note:
{{"type": "cultural_note", "speaker": "narrator", "language": "en", "text": "In Iceland, people use patronymic names...", "duration_estimate": 8}}

### 5. CLOSING SEGMENTS

closing_summary:
{{"type": "closing_summary", "speaker": "narrator", "language": "en", "text": "This is the end of Unit {lesson_number} and the end of today's lesson.", "duration_estimate": 5}}

closing_instructions:
{{"type": "closing_instructions", "speaker": "narrator", "language": "en", "text": "For best results, continue with Unit {next_lesson} tomorrow.", "duration_estimate": 4}}

## BACKWARD BUILD-UP EXAMPLES

Use the phonetic hints to decompose words from END to START:

Word: "Afsakið" (phonetic: AHF-sa-kith, meaning: "excuse me")
→ "kið" → "sakið" → "Af" → "Afsakið"

Word: "skilur" (phonetic: SKI-lur, meaning: "understand")
→ "lur" → "skilur"

Word: "smávegis" (phonetic: SMOW-vey-is, meaning: "a little")
→ "is" → "vegis" → "smá" → "smávegis"

## CRITICAL REQUIREMENTS

1. EVERY new word MUST have backward build-up (syllable decomposition)
2. Use VARIABLE pause durations based on the pause guide above
3. Opening MUST include: title → instruction → full dialogue
4. Closing MUST include: summary → next-steps instructions
5. Total segments must sum to approximately 1800 seconds
6. Each new word appears 7-10 times throughout lesson
7. Alternate between native_female and native_male speakers
8. Progressive context: word → phrase → sentence → dialogue

## VOCABULARY SUMMARY FORMAT

{{
  "word": "target word",
  "translation": "English",
  "introduced_at_second": 60,
  "repetitions_at_seconds": [65, 90, 180, 600, 1200]
}}

Generate the complete lesson script now. Output ONLY the JSON object."""


CUSTOM_LESSON_PROMPT = """Create an authentic Pimsleur-style lesson from user-provided text.

## SOURCE TEXT ({target_language})
{source_text}

## TASK
1. Extract 10-15 key vocabulary words and phrases from the text
2. Create a 15-20 minute lesson (900-1200 seconds) teaching this vocabulary
3. Follow authentic Pimsleur patterns including BACKWARD BUILD-UP

## OUTPUT FORMAT

{{
  "lesson_id": "custom",
  "title": "Custom Lesson",
  "total_duration_target": 1000,
  "segments": [/* array of segments */],
  "vocabulary_summary": [/* extracted vocabulary */]
}}

## SEGMENT TYPES

### 1. OPENING (30-45 seconds)

{{"type": "opening_title", "speaker": "narrator", "language": "en", "text": "This is your custom {target_language} lesson.", "duration_estimate": 3}}
{{"type": "opening_instruction", "speaker": "narrator", "language": "en", "text": "In this lesson, you'll learn vocabulary from a text you provided.", "duration_estimate": 4}}

### 2. NEW WORD INTRODUCTION (MANDATORY - use for EVERY word)

CRITICAL: Every word MUST have backward build-up!

Step 1 - Context:
{{"type": "instruction", "speaker": "narrator", "language": "en", "text": "The word for 'English meaning' is:", "duration_estimate": 3}}

Step 2 - First model:
{{"type": "native_model", "speaker": "native_female", "language": "{lang_code}", "text": "word", "duration_estimate": 2}}

Step 3 - Build-up instruction:
{{"type": "instruction", "speaker": "narrator", "language": "en", "text": "Listen and repeat from the end.", "duration_estimate": 2}}

Step 4 - BACKWARD BUILD-UP (syllables END to START):
{{"type": "syllable_practice", "speaker": "native_female", "language": "{lang_code}", "text": "last_syllable", "duration_estimate": 1}}
{{"type": "pause", "duration": 2.2, "purpose": "syllable_repetition"}}
{{"type": "syllable_practice", "speaker": "native_female", "language": "{lang_code}", "text": "more_syllables", "duration_estimate": 1}}
{{"type": "pause", "duration": 2.2, "purpose": "syllable_repetition"}}

Step 5 - Complete word:
{{"type": "native_model", "speaker": "native_female", "language": "{lang_code}", "text": "complete_word", "duration_estimate": 2}}
{{"type": "pause", "duration": 2.5, "purpose": "user_repetition"}}

Step 6 - Comprehension check:
{{"type": "comprehension_question", "speaker": "narrator", "language": "en", "text": "How do you say 'English'?", "expected_response": "word", "duration_estimate": 3}}
{{"type": "pause", "duration": 3.5, "purpose": "user_response"}}
{{"type": "model_answer", "speaker": "native_female", "language": "{lang_code}", "text": "word", "duration_estimate": 2}}

### 3. PRACTICE SEGMENTS

{{"type": "comprehension_question", "speaker": "narrator", "language": "en", "text": "How do you say 'X'?", "expected_response": "answer", "duration_estimate": 3}}
{{"type": "pause", "duration": 3.5, "purpose": "user_response"}}
{{"type": "model_answer", "speaker": "native_male", "language": "{lang_code}", "text": "answer", "duration_estimate": 2}}

{{"type": "prompt_for_composition", "speaker": "narrator", "language": "en", "text": "Try to say 'phrase'.", "expected_response": "phrase", "duration_estimate": 3}}
{{"type": "pause", "duration": 4.5, "purpose": "composition"}}
{{"type": "native_model", "speaker": "native_female", "language": "{lang_code}", "text": "phrase", "duration_estimate": 3}}

### 4. CLOSING (20-25 seconds)

{{"type": "closing_summary", "speaker": "narrator", "language": "en", "text": "This is the end of your custom lesson.", "duration_estimate": 3}}
{{"type": "closing_instructions", "speaker": "narrator", "language": "en", "text": "Review this lesson again tomorrow for best results.", "duration_estimate": 4}}

## PAUSE DURATION GUIDE

- syllable_repetition: 2.0-2.2 seconds
- user_repetition: 2.2-2.5 seconds
- user_response: 3.0-4.0 seconds
- composition: 4.0-5.0 seconds
- transition: 0.8-1.2 seconds

## BACKWARD BUILD-UP

For each word, break into syllables from END to START:
- "góðan" → "ðan" → "góðan"
- "takk" → "takk" (single syllable, just repeat)
- "íslensku" → "ku" → "lensku" → "ís" → "íslensku"

## CRITICAL REQUIREMENTS

1. EVERY new word MUST have backward build-up
2. Use VARIABLE pause durations (not fixed 3s)
3. Each word appears 5-7 times throughout lesson
4. Alternate native_female and native_male speakers
5. Include comprehension questions for each word
6. Do NOT reproduce copyrighted source text verbatim
7. Total duration ~1000 seconds (15-20 minutes)

Generate the complete lesson script now. Output ONLY the JSON object."""


def get_lesson_generation_prompt(
    target_language: str,
    lang_code: str,
    cefr_level: str,
    lesson_number: int,
    lesson_title: str,
    theme: str,
    new_vocabulary: list,
    review_vocabulary: list,
    opening_dialogue: list = None,
    grammar_notes: list = None,
    phrases: list = None,
) -> tuple[str, str]:
    """
    Generate system and user prompts for lesson generation.

    Args:
        target_language: Full language name (e.g., "Icelandic")
        lang_code: ISO code (e.g., "is")
        cefr_level: CEFR level (A1, A2, B1) - for backwards compatibility
        lesson_number: Lesson number (1-30)
        lesson_title: Title for the lesson
        theme: Theme/topic for vocabulary
        new_vocabulary: List of new vocab dicts with phonetic hints
        review_vocabulary: List of review vocab dicts
        opening_dialogue: Optional list of dialogue lines
        grammar_notes: Optional list of grammar notes to incorporate
        phrases: Optional list of key phrases to teach

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Map CEFR to Pimsleur level
    level_map = {"A1": 1, "A2": 2, "B1": 3}
    pimsleur_level = level_map.get(cefr_level, 1)

    # Format opening dialogue
    if opening_dialogue:
        dialogue_json = json.dumps(opening_dialogue, indent=2, ensure_ascii=False)
    else:
        dialogue_json = "[]  // No opening dialogue provided - create one based on vocabulary"

    # Build additional context section
    additional_context = ""
    if grammar_notes:
        additional_context += "\n## GRAMMAR NOTES TO INCORPORATE\n"
        for note in grammar_notes:
            additional_context += f"- {note}\n"
    if phrases:
        additional_context += "\n## KEY PHRASES TO TEACH\n"
        additional_context += json.dumps(phrases, indent=2, ensure_ascii=False)

    user_prompt = PIMSLEUR_LESSON_USER_PROMPT.format(
        target_language=target_language,
        lang_code=lang_code,
        cefr_level=cefr_level,
        pimsleur_level=pimsleur_level,
        lesson_number=lesson_number,
        lesson_title=lesson_title,
        theme=theme,
        next_lesson=lesson_number + 1,
        opening_dialogue_json=dialogue_json,
        new_vocabulary_json=json.dumps(new_vocabulary, indent=2, ensure_ascii=False),
        review_vocabulary_json=json.dumps(review_vocabulary, indent=2, ensure_ascii=False),
    )

    # Append additional context if present
    if additional_context:
        user_prompt += additional_context

    return PIMSLEUR_LESSON_SYSTEM_PROMPT, user_prompt


def get_custom_lesson_prompt(
    target_language: str,
    lang_code: str,
    source_text: str,
) -> tuple[str, str]:
    """
    Generate prompts for custom lesson from user text.

    Args:
        target_language: Full language name
        lang_code: ISO language code (e.g., "is")
        source_text: User-provided text in target language

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    user_prompt = CUSTOM_LESSON_PROMPT.format(
        target_language=target_language,
        lang_code=lang_code,
        source_text=source_text,
    )

    return PIMSLEUR_LESSON_SYSTEM_PROMPT, user_prompt
