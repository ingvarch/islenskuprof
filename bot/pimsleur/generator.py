"""
Pimsleur lesson script generator using LLM.
"""

import json
import logging
import re
from typing import Optional

from bot.openrouter_service import OpenRouterService
from bot.pimsleur.config import (
    CUSTOM_OPENING_TITLE_FORMAT,
    PAUSE_LEARNING,
    PAUSE_REPETITION,
    PAUSE_THINKING,
    PAUSE_RECALL,
    PAUSE_COMPOSITION,
    PAUSE_TRANSITION,
    PAUSE_REFLECTION,
    SEGMENT_TYPES,
    NATIVE_INSTRUCTION_START_UNIT,
    NATIVE_INSTRUCTION_FULL_UNIT,
)
from bot.pimsleur.prompts import (
    get_lesson_generation_prompt,
    get_custom_vocabulary_prompt,
)
from bot.pimsleur.vocabulary_manager import VocabularyProgressionManager

logger = logging.getLogger(__name__)


class PimsleurLessonGenerator:
    """
    Generates Pimsleur-style lesson scripts using LLM.
    """

    def __init__(self, language_config=None):
        """
        Initialize lesson generator.

        Args:
            language_config: Optional language configuration object
        """
        self.ai_service = OpenRouterService()
        self.lang_config = language_config
        self._lang_code = language_config.code if language_config else "is"
        self._language_name = language_config.name if language_config else "Icelandic"
        self.vocab_manager = VocabularyProgressionManager(language_code=self._lang_code)

    def generate_lesson_script(
        self,
        level: str,
        lesson_number: int,
        theme: Optional[str] = None,
        title: Optional[str] = None,
    ) -> dict:
        """
        Generate a complete Pimsleur lesson script.

        Args:
            level: Level identifier (can be "A1"/"A2"/"B1" for backwards compat, or 1/2/3)
            lesson_number: Lesson/unit number (1-30)
            theme: Optional theme override
            title: Optional title override

        Returns:
            Lesson script dictionary ready for audio generation
        """
        # Convert CEFR level to numeric if needed (backwards compatibility)
        level_map = {"A1": 1, "A2": 2, "B1": 3}
        numeric_level = level_map.get(level, int(level) if str(level).isdigit() else 1)

        # Get vocabulary for this unit
        vocab = self.vocab_manager.get_lesson_vocabulary(numeric_level, lesson_number)

        # Get theme if not provided
        if not theme:
            theme = self.vocab_manager.get_theme_for_unit(numeric_level, lesson_number)

        # Get title if not provided
        if not title:
            title = self.vocab_manager.get_unit_title(numeric_level, lesson_number)

        # Get opening dialogue (critical for real Pimsleur pattern)
        opening_dialogue = self.vocab_manager.get_opening_dialogue(
            numeric_level, lesson_number
        )

        # Get grammar notes and phrases for context
        grammar_notes = self.vocab_manager.get_grammar_notes(
            numeric_level, lesson_number
        )
        phrases = self.vocab_manager.get_phrases(numeric_level, lesson_number)

        logger.info(
            f"Generating script for Level {numeric_level} Unit {lesson_number}: {title} "
            f"({len(opening_dialogue)} dialogue lines, {len(grammar_notes)} grammar notes)"
        )

        # Prepare prompts
        system_prompt, user_prompt = get_lesson_generation_prompt(
            target_language=self._language_name,
            lang_code=self._lang_code,
            cefr_level=level,  # Keep original for prompt compatibility
            lesson_number=lesson_number,
            lesson_title=title,
            theme=theme,
            new_vocabulary=vocab["new"],
            review_vocabulary=vocab["review"],
            opening_dialogue=opening_dialogue,
            grammar_notes=grammar_notes,
            phrases=phrases,
        )

        # Generate script via LLM
        try:
            response = self.ai_service.generate_with_custom_prompt(
                system_message=system_prompt,
                user_message=user_prompt,
                max_tokens=16000,  # Lesson scripts are very long (~30 min content)
            )

            # Parse JSON response
            script = self._parse_script_response(response)

            # Validate and enhance script
            script = self._validate_and_enhance_script(
                script=script,
                level=numeric_level,
                lesson_number=lesson_number,
                vocab=vocab,
                opening_dialogue=opening_dialogue,
            )

            logger.info(
                f"Generated script with {len(script.get('segments', []))} segments, "
                f"estimated duration: {self._estimate_duration(script)}s"
            )

            return script

        except Exception as e:
            logger.error(f"Error generating lesson script: {e}")
            raise

    def generate_custom_lesson_script(
        self, source_text: str, difficulty_level: str = "1"
    ) -> dict:
        """
        Generate a custom lesson script from user-provided text using two-step process.

        Step 1: Creative agent generates vocabulary structure (dialogue, words, phrases)
        Step 2: Structural agent generates full Pimsleur lesson

        Args:
            source_text: Text in target language provided by user
            difficulty_level: User-selected or auto-detected difficulty (1, 2, or 3)

        Returns:
            Lesson script dictionary
        """
        # Import validator here to avoid circular imports
        from bot.pimsleur.input_validator import (
            validate_user_input,
            sanitize_user_input,
        )

        # Validate input first
        is_valid, error_msg = validate_user_input(source_text)
        if not is_valid:
            raise ValueError(f"Invalid input: {error_msg}")

        # Sanitize input
        source_text = sanitize_user_input(source_text)

        logger.info(
            f"[Custom Lesson] Starting two-step generation from "
            f"{len(source_text)} chars of text"
        )

        # Step 1: Generate vocabulary structure
        vocab_data = self._generate_custom_vocabulary(source_text)

        # Step 2: Generate full lesson using the vocabulary structure
        logger.info(
            f"[Custom Lesson] Step 2: Generating full lesson script "
            f"(title: {vocab_data.get('title', 'Custom Lesson')})"
        )

        # Prepare vocabulary in the format expected by lesson generator
        new_vocabulary = vocab_data.get("vocabulary", [])
        opening_dialogue = vocab_data.get("opening_dialogue", [])
        grammar_notes = vocab_data.get("grammar_notes", [])
        phrases = vocab_data.get("phrases", [])

        logger.info(
            f"[Custom Lesson] Vocabulary structure: {len(new_vocabulary)} words, "
            f"{len(opening_dialogue)} dialogue lines, {len(phrases)} phrases"
        )

        # Use the standard lesson generation prompt with custom vocabulary
        system_prompt, user_prompt = get_lesson_generation_prompt(
            target_language=self._language_name,
            lang_code=self._lang_code,
            cefr_level="A1",  # Default level for custom lessons
            lesson_number=0,  # Custom lesson
            lesson_title=vocab_data.get("title", "Custom Lesson"),
            theme=vocab_data.get("theme", "custom"),
            new_vocabulary=new_vocabulary,
            review_vocabulary=[],  # No review for custom lessons
            opening_dialogue=opening_dialogue,
            grammar_notes=grammar_notes,
            phrases=phrases,
        )

        try:
            response = self.ai_service.generate_with_custom_prompt(
                system_message=system_prompt,
                user_message=user_prompt,
                max_tokens=8000,  # Reduced for compatibility with free models
            )

            script = self._parse_script_response(response)

            # Inject opening dialogue from Step 1 (with translations)
            if opening_dialogue:
                self._inject_opening_dialogue_segment(script, opening_dialogue)
                logger.info(
                    f"[Custom Lesson] Injected opening dialogue with "
                    f"{len(opening_dialogue)} lines"
                )

            # Replace opening_title with custom format for personalized lessons
            self._replace_opening_title_for_custom(script, difficulty_level)

            # Add metadata for custom lessons
            script["is_custom"] = True
            script["source_text_length"] = len(source_text)
            script["custom_vocabulary"] = vocab_data

            # Create display data in the format expected by lesson_formatter
            script["display_data"] = self._create_display_data_from_vocab(vocab_data)

            # Calculate duration
            script["calculated_duration"] = self._estimate_duration(script)

            logger.info(
                f"[Custom Lesson] Complete! {len(script.get('segments', []))} segments, "
                f"~{script['calculated_duration']}s duration"
            )

            return script

        except Exception as e:
            logger.error(f"[Custom Lesson] Step 2 failed: {e}")
            raise

    def _generate_custom_vocabulary(self, source_text: str) -> dict:
        """
        Step 1: Generate vocabulary structure from user input.

        Uses creative agent to:
        - Analyze input and identify key vocabulary
        - Create a realistic scenario connecting the words
        - Generate an opening dialogue using the vocabulary
        - Extract grammar notes and useful phrases

        Args:
            source_text: User-provided words or text

        Returns:
            Vocabulary structure dict with dialogue, vocabulary, phrases, grammar_notes
        """
        logger.info(
            "[Custom Lesson] Step 1: Generating vocabulary structure from input"
        )

        system_prompt, user_prompt = get_custom_vocabulary_prompt(
            target_language=self._language_name,
            lang_code=self._lang_code,
            source_text=source_text,
        )

        try:
            response = self.ai_service.generate_with_custom_prompt(
                system_message=system_prompt,
                user_message=user_prompt,
                max_tokens=4000,
            )

            vocab_data = self._parse_script_response(response)

            # Log the generated structure
            logger.info(
                f"[Custom Lesson] Step 1 complete: "
                f"title='{vocab_data.get('title', 'Unknown')}', "
                f"theme='{vocab_data.get('theme', 'unknown')}', "
                f"vocabulary={len(vocab_data.get('vocabulary', []))} words, "
                f"dialogue={len(vocab_data.get('opening_dialogue', []))} lines"
            )

            return vocab_data

        except Exception as e:
            logger.error(f"[Custom Lesson] Step 1 failed: {e}")
            raise

    def _create_display_data_from_vocab(self, vocab_data: dict) -> dict:
        """
        Transform vocabulary data from Step 1 into display format.

        Converts the creative agent output into the format expected
        by lesson_formatter.py for Telegram message display.

        Args:
            vocab_data: Vocabulary structure from _generate_custom_vocabulary

        Returns:
            Display data dict compatible with format_header_message,
            format_vocabulary_message, and format_grammar_message
        """
        # Transform vocabulary: word_target -> word, word_native -> translation
        vocabulary = []
        for item in vocab_data.get("vocabulary", []):
            vocabulary.append(
                {
                    "word": item.get("word_target", ""),
                    "translation": item.get("word_native", ""),
                    "word_type": item.get("word_type", "word"),
                    "phonetic": item.get("phonetic", ""),
                }
            )

        # Phrases are already in correct format (target, translation)
        phrases = vocab_data.get("phrases", [])

        # Opening dialogue is already in correct format (target, translation)
        opening_dialogue = vocab_data.get("opening_dialogue", [])

        # Grammar notes are already strings
        grammar_notes = vocab_data.get("grammar_notes", [])

        return {
            "title": vocab_data.get("title", "Custom Lesson"),
            "theme": vocab_data.get("theme", "custom"),
            "opening_dialogue": opening_dialogue,
            "vocabulary": vocabulary,
            "phrases": phrases,
            "grammar_notes": grammar_notes,
        }

    def _clean_markdown_json(self, response: str) -> str:
        """Remove markdown code blocks from JSON response."""
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _repair_truncated_json(self, json_str: str) -> str:
        """Attempt to repair truncated JSON by adding missing closing brackets."""
        repaired = json_str.rstrip()

        # Remove incomplete trailing elements
        repaired = re.sub(r",\s*$", "", repaired)  # Trailing comma
        repaired = re.sub(r',\s*"[^"]*$', "", repaired)  # Incomplete key after comma
        repaired = re.sub(r':\s*"[^"]*$', "", repaired)  # Incomplete string value
        repaired = re.sub(r":\s*$", "", repaired)  # Trailing colon

        # Count brackets and add missing closers
        open_brackets = repaired.count("[") - repaired.count("]")
        open_braces = repaired.count("{") - repaired.count("}")

        # Add missing closers (arrays first, then objects)
        repaired += "]" * max(0, open_brackets)
        repaired += "}" * max(0, open_braces)

        return repaired

    def _parse_script_response(self, response: str) -> dict:
        """Parse LLM response into script dictionary with repair for truncated JSON."""
        cleaned = self._clean_markdown_json(response)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {e}")
            logger.debug(f"Response tail (last 200 chars): ...{cleaned[-200:]}")

            # Attempt to repair truncated JSON
            logger.info("Attempting to repair truncated JSON...")
            repaired = self._repair_truncated_json(cleaned)

            try:
                result = json.loads(repaired)
                logger.info("JSON repair successful")
                return result
            except json.JSONDecodeError as e2:
                logger.error(f"JSON repair failed: {e2}")
                logger.debug(f"Repaired tail: ...{repaired[-200:]}")
                raise ValueError(f"Invalid JSON in LLM response: {e}")

    def _inject_opening_dialogue_segment(
        self,
        script: dict,
        opening_dialogue: list[dict],
    ) -> None:
        """
        Inject opening_dialogue segment from vocabulary bank data.

        This ensures the segment matches the authoritative vocabulary bank
        and includes translations for display purposes.

        Args:
            script: Script dictionary to modify
            opening_dialogue: List of dialogue lines with target/translation keys
        """
        if not opening_dialogue:
            return

        # Build lines with speaker alternation
        lines = []
        for i, line in enumerate(opening_dialogue):
            speaker = "native_female" if i % 2 == 0 else "native_male"
            lines.append(
                {
                    "speaker": speaker,
                    "text": line.get("target", ""),
                    "translation": line.get("translation", ""),
                }
            )

        # Create segment
        segment = {
            "type": "opening_dialogue",
            "lines": lines,
            "duration_estimate": len(lines) * 3,  # ~3s per line
        }

        # Find and remove any existing opening_dialogue segment
        segments = script.get("segments", [])
        segments[:] = [s for s in segments if s.get("type") != "opening_dialogue"]

        # Find position after opening_instruction
        insert_pos = 2  # Default after title + instruction
        for i, seg in enumerate(segments):
            if seg.get("type") == "opening_instruction":
                insert_pos = i + 1
                break

        segments.insert(insert_pos, segment)

    def _replace_opening_title_for_custom(
        self,
        script: dict,
        difficulty_level: str,
    ) -> None:
        """
        Replace the opening_title segment with a custom format for personalized lessons.

        Instead of "Level X, Unit Y", custom lessons say:
        "This is a personalized lesson. Based on provided words, difficulty level: X."

        Args:
            script: Script dictionary to modify
            difficulty_level: Difficulty level (1, 2, or 3)
        """
        segments = script.get("segments", [])

        # Find the opening_title segment
        for segment in segments:
            if segment.get("type") == "opening_title":
                segment["text"] = CUSTOM_OPENING_TITLE_FORMAT.format(
                    difficulty=difficulty_level
                )
                logger.info(
                    f"[Custom Lesson] Replaced opening_title with difficulty {difficulty_level}"
                )
                break

    def _validate_and_enhance_script(
        self,
        script: dict,
        level: int,
        lesson_number: int,
        vocab: dict,
        opening_dialogue: list[dict] = None,
    ) -> dict:
        """
        Validate and enhance the generated script.

        Args:
            script: Generated script dictionary
            level: Pimsleur level (1, 2, 3)
            lesson_number: Unit number
            vocab: Vocabulary data
            opening_dialogue: Opening dialogue from vocabulary bank

        Returns:
            Enhanced script dictionary
        """
        # Ensure required fields
        script.setdefault("lesson_id", lesson_number)
        script.setdefault("level", level)
        script.setdefault("segments", [])
        script.setdefault("vocabulary_summary", [])

        # Inject opening dialogue from vocabulary bank (replaces LLM-generated)
        if opening_dialogue:
            self._inject_opening_dialogue_segment(script, opening_dialogue)

        # Add review unit references
        review_units = self.vocab_manager.get_review_unit_ids(lesson_number)
        script["review_from_units"] = review_units

        # Store vocabulary data
        script["vocabulary_new"] = vocab["new"]
        script["vocabulary_review"] = vocab["review"]

        # Validate and fix segment types
        unknown_types = set()
        for segment in script.get("segments", []):
            seg_type = segment.get("type", "")
            if seg_type and seg_type not in SEGMENT_TYPES:
                unknown_types.add(seg_type)

        if unknown_types:
            logger.warning(f"Script contains unknown segment types: {unknown_types}")

        # Check for required Pimsleur structure elements
        segment_types_present = {s.get("type") for s in script.get("segments", [])}

        missing_critical = []
        if "opening_title" not in segment_types_present:
            missing_critical.append("opening_title")
        if "closing_summary" not in segment_types_present:
            missing_critical.append("closing_summary")
        if "syllable_practice" not in segment_types_present:
            logger.warning(
                "Script may be missing backward build-up (no syllable_practice)"
            )

        if missing_critical:
            logger.warning(
                f"Script missing critical Pimsleur elements: {missing_critical}"
            )

        # Check for instruction language evolution (units 11+ should have native instructions)
        has_native_instruction = "native_instruction" in segment_types_present
        if lesson_number >= NATIVE_INSTRUCTION_FULL_UNIT and not has_native_instruction:
            logger.warning(
                f"Unit {lesson_number} should use native language instructions "
                f"(Hlustaðu, Spurðu, etc.) but none found"
            )

        # Calculate actual duration
        script["calculated_duration"] = self._estimate_duration(script)

        # Add segment IDs for tracking
        for i, segment in enumerate(script.get("segments", [])):
            segment["segment_id"] = i

        # Add validation metadata
        script["validation"] = {
            "unknown_segment_types": list(unknown_types),
            "has_opening": "opening_title" in segment_types_present,
            "has_closing": "closing_summary" in segment_types_present,
            "has_backward_buildup": "syllable_practice" in segment_types_present,
            "has_native_instructions": has_native_instruction,
            "expected_native_instructions": lesson_number
            >= NATIVE_INSTRUCTION_START_UNIT,
        }

        return script

    def _estimate_duration(self, script: dict) -> int:
        """
        Estimate total duration of script in seconds.

        Uses variable pause durations based on cognitive load,
        following real Pimsleur patterns.

        Args:
            script: Lesson script dictionary

        Returns:
            Estimated duration in seconds
        """
        total = 0
        for segment in script.get("segments", []):
            seg_type = segment.get("type", "")

            if seg_type == "pause":
                # Use pause duration from segment, or estimate based on purpose
                purpose = segment.get("purpose", "")
                if "duration" in segment:
                    total += segment["duration"]
                elif purpose in ("user_repetition", "repeat"):
                    total += PAUSE_REPETITION
                elif purpose in ("user_response", "thinking"):
                    total += PAUSE_THINKING
                elif purpose in ("recall", "remember"):
                    total += PAUSE_RECALL
                elif purpose in ("composition", "user_composition"):
                    total += PAUSE_COMPOSITION
                elif purpose in ("reflection", "long_reflection"):
                    total += PAUSE_REFLECTION
                elif purpose == "transition":
                    total += PAUSE_TRANSITION
                else:
                    total += PAUSE_LEARNING  # Default

            elif seg_type == "syllable_practice":
                # Short TTS for syllables + learning pause
                total += segment.get("duration_estimate", 1.5)

            elif seg_type in ("opening_dialogue", "dialogue_segment"):
                # Dialogue segments typically longer
                total += segment.get("duration_estimate", 8)

            elif seg_type in (
                "native_model",
                "model_answer",
                "context_application",
                "review_in_context",
                "native_instruction",
                "grammar_drill",
            ):
                # Native speaker segments
                total += segment.get("duration_estimate", 3)

            elif seg_type in (
                "instruction",
                "comprehension_question",
                "prompt_for_composition",
                "prompt_for_question",
                "repeat_after",
                "grammar_explanation",
                "cultural_note",
                "opening_title",
                "opening_instruction",
                "opening_context",
                "opening_preview",
                "recall_question",
                "scenario_setup",
                "gender_explanation",
                "closing_summary",
                "closing_instructions",
            ):
                # Narrator segments - typically longer
                total += segment.get("duration_estimate", 4)

            else:
                # Default for unknown types
                total += segment.get("duration_estimate", 3)

        return int(total)

    def get_script_statistics(self, script: dict) -> dict:
        """
        Get statistics about a generated script.

        Args:
            script: Lesson script dictionary

        Returns:
            Statistics dictionary with Pimsleur-specific metrics
        """
        segments = script.get("segments", [])

        segment_types = {}
        for seg in segments:
            seg_type = seg.get("type", "unknown")
            segment_types[seg_type] = segment_types.get(seg_type, 0) + 1

        # Calculate pause time with variable durations
        pause_time = 0
        for seg in segments:
            if seg.get("type") == "pause":
                purpose = seg.get("purpose", "")
                if "duration" in seg:
                    pause_time += seg["duration"]
                elif purpose in ("user_repetition", "repeat"):
                    pause_time += PAUSE_REPETITION
                elif purpose in ("user_response", "thinking"):
                    pause_time += PAUSE_THINKING
                elif purpose in ("recall", "remember"):
                    pause_time += PAUSE_RECALL
                elif purpose in ("composition", "user_composition"):
                    pause_time += PAUSE_COMPOSITION
                elif purpose in ("reflection", "long_reflection"):
                    pause_time += PAUSE_REFLECTION
                else:
                    pause_time += PAUSE_LEARNING

        estimated_duration = self._estimate_duration(script)

        # Count Pimsleur-specific elements
        syllable_practice_count = segment_types.get("syllable_practice", 0)
        backward_buildup_sequences = (
            syllable_practice_count // 3
        )  # ~3 syllables per word

        return {
            "total_segments": len(segments),
            "segment_types": segment_types,
            "estimated_duration": estimated_duration,
            "estimated_minutes": round(estimated_duration / 60, 1),
            "pause_time": int(pause_time),
            "speaking_time": estimated_duration - int(pause_time),
            "new_vocabulary_count": len(script.get("vocabulary_new", [])),
            "review_vocabulary_count": len(script.get("vocabulary_review", [])),
            # Pimsleur-specific metrics
            "has_opening_structure": (
                segment_types.get("opening_title", 0) > 0
                and segment_types.get("opening_dialogue", 0) > 0
            ),
            "has_closing_structure": segment_types.get("closing_summary", 0) > 0,
            "backward_buildup_count": backward_buildup_sequences,
            "syllable_practice_count": syllable_practice_count,
            "comprehension_questions": segment_types.get("comprehension_question", 0),
            "composition_prompts": segment_types.get("prompt_for_composition", 0),
            # New segment type counts (from Units 11-20 analysis)
            "recall_questions": segment_types.get("recall_question", 0),
            "scenario_setups": segment_types.get("scenario_setup", 0),
            "grammar_drills": segment_types.get("grammar_drill", 0),
            "native_instructions": segment_types.get("native_instruction", 0),
            "gender_explanations": segment_types.get("gender_explanation", 0),
            "validation": script.get("validation", {}),
        }
