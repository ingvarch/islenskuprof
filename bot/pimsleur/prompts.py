"""
LLM prompt templates for Pimsleur lesson generation.
"""

PIMSLEUR_LESSON_SYSTEM_PROMPT = """You are an expert language curriculum designer specializing in the Pimsleur method for audio-based language learning.

Your task is to create lesson scripts that follow Pimsleur's core principles:

1. GRADUATED INTERVAL RECALL (Spaced Repetition):
   - New words must be repeated at increasing intervals: 5s, 25s, 2min, 10min, 20min
   - Each new word/phrase should appear 7-10 times minimum throughout the lesson
   - Review vocabulary from previous lessons at strategic intervals

2. ANTICIPATION PRINCIPLE:
   - Always prompt the learner before providing the answer
   - Allow 3-5 seconds pause for learner to formulate and speak their response
   - Follow with correct model answer spoken by native speaker
   - Learner then repeats after the native model

3. CORE VOCABULARY:
   - Introduce a specific number of NEW words/phrases per lesson (specified in request)
   - Build systematically on vocabulary from previous lessons
   - Focus on high-frequency, practical usage
   - Use words in context within short dialogues

4. LESSON STRUCTURE (30 minutes total = 1800 seconds):
   - Opening (60-90 sec): Welcome, brief context setting
   - New Material Introduction (600-720 sec): Introduce new vocabulary one by one
   - Spaced Practice (900-1080 sec): Main body with spaced repetitions and dialogues
   - Review/Closing (60-90 sec): Quick summary, preview of next lesson

You must output ONLY valid JSON. No markdown, no explanations, just the JSON object.
IMPORTANT: Output compact JSON without unnecessary whitespace to save tokens."""


PIMSLEUR_LESSON_USER_PROMPT = """Create a Pimsleur-style lesson script for {target_language} learners.

LESSON PARAMETERS:
- CEFR Level: {cefr_level}
- Lesson Number: {lesson_number} of 30
- Lesson Title: {lesson_title}
- Theme: {theme}
- Target Duration: 1800 seconds (30 minutes)

VOCABULARY TO INTRODUCE (NEW - first time):
{new_vocabulary_json}

VOCABULARY TO REVIEW (from previous lessons):
{review_vocabulary_json}

LANGUAGE-SPECIFIC NOTES:
- Target language: {target_language}
- Native language for instructions: English
- Speaker labels: Use "native_female" and "native_male" for target language speakers
- Speaker labels: Use "narrator" for English instructions

OUTPUT REQUIREMENTS:
Generate a JSON object with this exact structure:

{{
  "lesson_id": {lesson_number},
  "level": "{cefr_level}",
  "title": "{lesson_title}",
  "theme": "{theme}",
  "total_duration_target": 1800,
  "segments": [
    // Array of segment objects (see types below)
  ],
  "vocabulary_summary": [
    // Array of vocabulary objects with repetition timings
  ]
}}

SEGMENT TYPES:

1. Instruction (narrator in English):
{{
  "type": "instruction",
  "speaker": "narrator",
  "language": "en",
  "text": "Welcome to lesson one. Today we'll learn basic greetings.",
  "duration_estimate": 5
}}

2. New Word Introduction (MUST follow this exact sequence):
   a) First, narrator explains what we're learning:
{{
  "type": "instruction",
  "speaker": "narrator",
  "language": "en",
  "text": "The word for 'English meaning' is:",
  "duration_estimate": 3
}}
   b) Then native speaker says the word:
{{
  "type": "new_word",
  "speaker": "native_female",
  "language": "{lang_code}",
  "text": "the word in target language",
  "translation": "English translation",
  "duration_estimate": 2
}}

3. Prompt (narrator asks user to produce):
{{
  "type": "prompt",
  "speaker": "narrator",
  "language": "en",
  "text": "How do you say 'hello' in Icelandic?",
  "expected_response": "the expected word",
  "duration_estimate": 3
}}

4. Pause (for user response):
{{
  "type": "pause",
  "duration": 4,
  "purpose": "user_response"
}}

5. Model Answer (native speaker gives correct answer):
{{
  "type": "model_answer",
  "speaker": "native_male",
  "language": "{lang_code}",
  "text": "correct answer in target language",
  "duration_estimate": 2
}}

6. Repeat After instruction:
{{
  "type": "repeat_after",
  "speaker": "narrator",
  "language": "en",
  "text": "Listen and repeat.",
  "duration_estimate": 2
}}

7. Native Model (for repetition):
{{
  "type": "native_model",
  "speaker": "native_female",
  "language": "{lang_code}",
  "text": "word or phrase to repeat",
  "duration_estimate": 2
}}

8. Pause for repetition:
{{
  "type": "pause",
  "duration": 3,
  "purpose": "user_repetition"
}}

9. Dialogue Segment (short contextual dialogue):
{{
  "type": "dialogue_segment",
  "lines": [
    {{"speaker": "native_female", "text": "first line"}},
    {{"speaker": "native_male", "text": "response"}}
  ],
  "context": "Brief description of the dialogue scenario",
  "duration_estimate": 8
}}

CRITICAL REQUIREMENTS:
1. Total segment durations must sum to approximately 1800 seconds
2. Each new word must appear at least 7 times throughout the lesson
3. Alternate between male and female native speakers
4. Include short dialogues to show vocabulary in context
5. End with a brief closing that previews the next lesson
6. Vocabulary summary must include second marks for each repetition

MANDATORY WORD INTRODUCTION PATTERN (NEVER deviate from this):
Every time you introduce a new word, you MUST use this EXACT sequence:
1. instruction: Narrator says "The word for '[English translation]' is:"
2. new_word: Native speaker says the word in target language
3. repeat_after: Narrator says "Listen and repeat."
4. native_model: Native speaker says the word again
5. pause: 3 seconds for user repetition

Example for introducing "hello" (hallo):
{{"type": "instruction", "speaker": "narrator", "language": "en", "text": "The word for 'hello' is:", "duration_estimate": 2}}
{{"type": "new_word", "speaker": "native_female", "language": "{lang_code}", "text": "hallo", "translation": "hello", "duration_estimate": 2}}
{{"type": "repeat_after", "speaker": "narrator", "language": "en", "text": "Listen and repeat.", "duration_estimate": 2}}
{{"type": "native_model", "speaker": "native_female", "language": "{lang_code}", "text": "hallo", "duration_estimate": 2}}
{{"type": "pause", "duration": 3, "purpose": "user_repetition"}}

NEVER introduce a new word without first having the narrator explain what it means in English!

VOCABULARY SUMMARY FORMAT:
{{
  "word": "the target word",
  "translation": "English meaning",
  "introduced_at_second": 120,
  "repetitions_at_seconds": [125, 150, 270, 720, 1380]
}}

Generate the complete lesson script now. Output ONLY the JSON object."""


CUSTOM_LESSON_PROMPT = """Create a Pimsleur-style lesson from the following user-provided text.

SOURCE TEXT ({target_language}):
{source_text}

TASK:
1. Extract 10-15 key vocabulary words and phrases from the text
2. Create a 15-20 minute Pimsleur-style lesson teaching this vocabulary
3. Follow Pimsleur principles (spaced repetition, anticipation, repetition)

OUTPUT FORMAT - JSON with this EXACT structure:
{{
  "lesson_id": "custom",
  "title": "Custom Lesson",
  "total_duration_target": 900,
  "segments": [
    // Array of segment objects
  ],
  "vocabulary_summary": []
}}

SEGMENT TYPES (use these EXACTLY):

1. Instruction (narrator in English):
{{"type": "instruction", "speaker": "narrator", "language": "en", "text": "Welcome to your custom lesson.", "duration_estimate": 5}}

2. New Word Introduction - ALWAYS use this sequence:
{{"type": "instruction", "speaker": "narrator", "language": "en", "text": "The word for 'hello' is:", "duration_estimate": 2}}
{{"type": "new_word", "speaker": "native_female", "language": "{lang_code}", "text": "hallo", "translation": "hello", "duration_estimate": 2}}
{{"type": "repeat_after", "speaker": "narrator", "language": "en", "text": "Listen and repeat.", "duration_estimate": 2}}
{{"type": "native_model", "speaker": "native_female", "language": "{lang_code}", "text": "hallo", "duration_estimate": 2}}
{{"type": "pause", "duration": 3, "purpose": "user_repetition"}}

3. Prompt (ask user to produce):
{{"type": "prompt", "speaker": "narrator", "language": "en", "text": "How do you say 'hello'?", "expected_response": "hallo", "duration_estimate": 3}}

4. Pause:
{{"type": "pause", "duration": 4, "purpose": "user_response"}}

5. Model Answer:
{{"type": "model_answer", "speaker": "native_male", "language": "{lang_code}", "text": "hallo", "duration_estimate": 2}}

IMPORTANT:
- Alternate between "native_female" and "native_male" speakers
- Every segment MUST have a "text" field (except pause)
- Include 7+ repetitions of each new word throughout the lesson

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
) -> tuple[str, str]:
    """
    Generate system and user prompts for lesson generation.

    Args:
        target_language: Full language name (e.g., "Icelandic")
        lang_code: ISO code (e.g., "is")
        cefr_level: CEFR level (A1, A2, B1)
        lesson_number: Lesson number (1-30)
        lesson_title: Title for the lesson
        theme: Theme/topic for vocabulary
        new_vocabulary: List of new vocab dicts
        review_vocabulary: List of review vocab dicts

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    import json

    user_prompt = PIMSLEUR_LESSON_USER_PROMPT.format(
        target_language=target_language,
        lang_code=lang_code,
        cefr_level=cefr_level,
        lesson_number=lesson_number,
        lesson_title=lesson_title,
        theme=theme,
        new_vocabulary_json=json.dumps(new_vocabulary, indent=2, ensure_ascii=False),
        review_vocabulary_json=json.dumps(review_vocabulary, indent=2, ensure_ascii=False),
    )

    return PIMSLEUR_LESSON_SYSTEM_PROMPT, user_prompt


def get_custom_lesson_prompt(target_language: str, lang_code: str, source_text: str) -> tuple[str, str]:
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
