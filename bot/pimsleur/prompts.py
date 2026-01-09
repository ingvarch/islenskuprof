"""
LLM prompt templates for Spaced Audio Course lesson generation.

Based on analysis of 30 real audio lesson transcriptions.
Key patterns: backward build-up, variable pauses, progressive context building,
instruction language evolution, grammar drills.

Note: Uses "Spaced Audio Course" instead of trademark names.
"""

import json


PIMSLEUR_LESSON_SYSTEM_PROMPT = """You are an expert language curriculum designer specializing in the spaced repetition audio method for language learning.

Your task is to create lesson scripts that follow proven audio-lingual methodology based on analysis of 30 transcribed lessons.

IMPORTANT: Do NOT use the word "Pimsleur" in any generated text. Use "Spaced Audio Course" or simply describe the lesson.

## CORE SPACED AUDIO PRINCIPLES

### 1. BACKWARD BUILD-UP (CRITICAL - This is the #1 audio-lingual technique)
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
- Review vocabulary from previous lessons using "Do you remember how to say..."

### 3. ANTICIPATION PRINCIPLE
- Always prompt the learner BEFORE providing the answer
- Use varied question patterns (see Question Variation section)
- Variable pause duration based on difficulty (see pause guide)
- Follow with correct model answer spoken by native speaker

### 4. PROGRESSIVE CONTEXT BUILDING
Every word progresses through these stages:
1. Single word isolation
2. Word in simple phrase
3. Phrase in complete sentence
4. Sentence in dialogue context

### 5. INSTRUCTION LANGUAGE EVOLUTION (Critical for units 6+)
- Units 1-5: All instructions in English
- Units 6-10: Mix English with some target language commands
- Units 11+: Use target language for common instructions:
  * "Hlustaðu" (Listen) instead of "Listen"
  * "Hlustaðu og endurtaktu" instead of "Listen and repeat"
  * "Spurðu" instead of "Ask"
  * "Svaraðu spurningum" (Answer questions)

### 6. LESSON STRUCTURE (30 minutes = 1800 seconds)

**OPENING (30-60 seconds):**
- opening_title: "This is Level Y, Unit X of your [Language] Spaced Audio Course"
- opening_context (units 15+): Brief context setup before dialogue
- opening_preview (optional): "You will hear [phrase] which means [translation]"
- opening_instruction: "Listen to this conversation" / "Hlustaðu á þetta samtal"
- opening_dialogue: Full native conversation (4-8 lines)

**NEW MATERIAL (600-720 seconds):**
- Introduce new vocabulary with backward build-up
- Include gender/grammar explanations where relevant
- Each word gets full introduction sequence (~60 seconds per word)

**SPACED PRACTICE (900-1080 seconds):**
- Review new words at intervals
- Use recall_question for previous unit vocabulary
- Use scenario_setup for contextualized practice
- Include grammar_drill for gender/conjugation practice
- Short dialogues showing vocabulary in context

**CLOSING (25-30 seconds):**
- closing_summary: "This is the end of Unit X"
- closing_instructions: "For best results, continue with Unit X+1 tomorrow"

## PAUSE DURATION GUIDE (CRITICAL - Variable pauses!)

| Pause Type | Duration | When to Use |
|------------|----------|-------------|
| syllable_pause | 2.0-2.2s | After each syllable in backward build-up |
| learning_pause | 2.2-2.5s | After native speaker models complete word |
| thinking_pause | 3.0-4.0s | After "How do you say X?" questions |
| recall_pause | 3.4-4.0s | After "Do you remember how to say..." |
| composition_pause | 4.0-5.0s | When student creates new sentences |
| confirmation_pause | 1.8-2.2s | After providing correct answer |
| transition_pause | 0.8-1.2s | Between major segments |
| reflection_pause | 6.5-8.7s | For complex reflection in later units |

## QUESTION VARIATION PATTERNS

Use variety in question phrasing (from real audio lessons):
- "How do you say X?" (standard)
- "How would you say X?" (conditional)
- "How does he/she tell you that..." (third person)
- "How do you ask him/her if..." (indirect question)
- "Do you remember how to say..." (recall from previous units)
- "Now say..." / "Segðu núna..." (direct command)
- "Ask him/her..." / "Spurðu..." (question formation)

## GRAMMAR DRILL PATTERN (Units 11+)

For gender/conjugation teaching:
1. Explain grammar point: "Beer is a masculine word. Here's how to say no beer."
2. Model the form: native speaker says it
3. Drill variations: masculine, feminine, neuter forms
4. Practice in context

Example:
- "ekkert" (neuter - no wine)
- "engan" (masculine - no beer)
- "enga" (feminine - no króna)
- "engar" (feminine plural - no krónur)

You must output ONLY valid JSON. No markdown, no explanations.
Output compact JSON without unnecessary whitespace."""


PIMSLEUR_LESSON_USER_PROMPT = """Create a spaced repetition audio lesson script for {target_language} learners.

## LESSON PARAMETERS
- Level: {pimsleur_level} (CEFR: {cefr_level})
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
{{"type": "opening_title", "speaker": "narrator", "language": "en", "text": "This is Level {pimsleur_level}, Unit {lesson_number} of your {target_language} Spaced Audio Course.", "duration_estimate": 5}}

opening_context (for units 15+, context before dialogue):
{{"type": "opening_context", "speaker": "narrator", "language": "en", "text": "John has gone to visit his friend. You will hear him asking for directions.", "duration_estimate": 5}}

opening_preview (optional - preview key phrase):
{{"type": "opening_preview", "speaker": "narrator", "language": "en", "text": "You will hear 'Hvert ertu að fara?' which means 'Where are you going?'", "duration_estimate": 4}}

opening_instruction (use native language for units 11+):
{{"type": "opening_instruction", "speaker": "narrator", "language": "en", "text": "Listen to this {target_language} conversation.", "duration_estimate": 3}}
For units 11+: {{"type": "native_instruction", "speaker": "native_female", "language": "{lang_code}", "text": "Hlustaðu á þetta samtal.", "duration_estimate": 2}}

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

comprehension_question (standard "How do you say"):
{{"type": "comprehension_question", "speaker": "narrator", "language": "en", "text": "How do you say 'X' in {target_language}?", "expected_response": "answer", "duration_estimate": 3}}

recall_question (for vocabulary from PREVIOUS units):
{{"type": "recall_question", "speaker": "narrator", "language": "en", "text": "Do you remember how to say 'hello'?", "expected_response": "answer", "duration_estimate": 4}}
{{"type": "pause", "duration": 3.4, "purpose": "recall"}}

prompt_for_composition:
{{"type": "prompt_for_composition", "speaker": "narrator", "language": "en", "text": "Try to say 'I understand a little {target_language}'.", "expected_response": "expected phrase", "duration_estimate": 4}}

prompt_for_question (use native language for units 11+):
{{"type": "prompt_for_question", "speaker": "narrator", "language": "en", "text": "Ask her if she understands English.", "expected_response": "expected question", "duration_estimate": 4}}
For units 11+: {{"type": "native_instruction", "speaker": "native_female", "language": "{lang_code}", "text": "Spurðu.", "duration_estimate": 1}}

scenario_setup (contextualized practice):
{{"type": "scenario_setup", "speaker": "narrator", "language": "en", "text": "Suppose you're hosting a party for some business associates. Say to one of the guests, please come in.", "duration_estimate": 6}}
{{"type": "pause", "duration": 4.5, "purpose": "composition"}}

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

gender_explanation (for gender-specific vocabulary, units 11+):
{{"type": "gender_explanation", "speaker": "narrator", "language": "en", "text": "Beer is a masculine word. Here's how to say 'no beer' or 'not any beer'.", "duration_estimate": 5}}

grammar_drill (drill gender/conjugation variations):
{{"type": "grammar_drill", "speaker": "native_female", "language": "{lang_code}", "text": "engan bjór", "grammar_form": "masculine_accusative", "duration_estimate": 2}}
{{"type": "pause", "duration": 2.5, "purpose": "user_repetition"}}
{{"type": "grammar_drill", "speaker": "native_female", "language": "{lang_code}", "text": "ekkert vín", "grammar_form": "neuter_accusative", "duration_estimate": 2}}
{{"type": "pause", "duration": 2.5, "purpose": "user_repetition"}}

cultural_note:
{{"type": "cultural_note", "speaker": "narrator", "language": "en", "text": "In Iceland, people use patronymic names...", "duration_estimate": 8}}

### 5. CLOSING SEGMENTS

closing_summary:
{{"type": "closing_summary", "speaker": "narrator", "language": "en", "text": "This is the end of Level {pimsleur_level}, Unit {lesson_number}.", "duration_estimate": 4}}

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
9. For units 6+: Start mixing target language instructions
10. For units 11+: Use primarily target language for commands (Hlustaðu, Spurðu, etc.)
11. Use recall_question ("Do you remember...") for review vocabulary
12. Use scenario_setup for contextualized practice in later units
13. Include gender_explanation and grammar_drill for grammar-heavy vocabulary

## VOCABULARY SUMMARY FORMAT

{{
  "word": "target word",
  "translation": "English",
  "introduced_at_second": 60,
  "repetitions_at_seconds": [65, 90, 180, 600, 1200]
}}

Generate the complete lesson script now. Output ONLY the JSON object."""


CUSTOM_LESSON_PROMPT = """Create a spaced repetition audio lesson from user-provided text.

## SOURCE TEXT ({target_language})
{source_text}

## TASK
1. Extract 10-15 key vocabulary words and phrases from the text
2. Create a 15-20 minute lesson (900-1200 seconds) teaching this vocabulary
3. Follow authentic spaced audio patterns including BACKWARD BUILD-UP

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

{{"type": "opening_title", "speaker": "narrator", "language": "en", "text": "Welcome to your custom {target_language} Spaced Audio Lesson.", "duration_estimate": 4}}
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
    # Map CEFR to course level
    level_map = {"A1": 1, "A2": 2, "B1": 3}
    pimsleur_level = level_map.get(cefr_level, 1)

    # Format opening dialogue
    if opening_dialogue:
        dialogue_json = json.dumps(opening_dialogue, indent=2, ensure_ascii=False)
    else:
        dialogue_json = (
            "[]  // No opening dialogue provided - create one based on vocabulary"
        )

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
        review_vocabulary_json=json.dumps(
            review_vocabulary, indent=2, ensure_ascii=False
        ),
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
