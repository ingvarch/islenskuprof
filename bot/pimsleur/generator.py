"""
Pimsleur lesson script generator using LLM.
"""

import json
import logging
from typing import Optional

from bot.openrouter_service import OpenRouterService
from bot.pimsleur.config import (
    PAUSE_SYLLABLE,
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
    get_custom_lesson_prompt,
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
        opening_dialogue = self.vocab_manager.get_opening_dialogue(numeric_level, lesson_number)

        # Get grammar notes and phrases for context
        grammar_notes = self.vocab_manager.get_grammar_notes(numeric_level, lesson_number)
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
            )

            logger.info(
                f"Generated script with {len(script.get('segments', []))} segments, "
                f"estimated duration: {self._estimate_duration(script)}s"
            )

            return script

        except Exception as e:
            logger.error(f"Error generating lesson script: {e}")
            raise

    def generate_custom_lesson_script(self, source_text: str) -> dict:
        """
        Generate a custom lesson script from user-provided text.

        Args:
            source_text: Text in target language provided by user

        Returns:
            Lesson script dictionary
        """
        logger.info(f"Generating custom lesson from {len(source_text)} chars of text")

        system_prompt, user_prompt = get_custom_lesson_prompt(
            target_language=self._language_name,
            lang_code=self._lang_code,
            source_text=source_text,
        )

        try:
            response = self.ai_service.generate_with_custom_prompt(
                system_message=system_prompt,
                user_message=user_prompt,
                max_tokens=6000,
            )

            script = self._parse_script_response(response)

            # Add metadata for custom lessons
            script["is_custom"] = True
            script["source_text_length"] = len(source_text)

            return script

        except Exception as e:
            logger.error(f"Error generating custom lesson: {e}")
            raise

    def _parse_script_response(self, response: str) -> dict:
        """
        Parse LLM response into script dictionary.

        Args:
            response: Raw LLM response text

        Returns:
            Parsed script dictionary
        """
        # Clean up response - remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse script JSON: {e}")
            logger.debug(f"Response was: {cleaned[:500]}...")
            raise ValueError(f"Invalid JSON in LLM response: {e}")

    def _validate_and_enhance_script(
        self,
        script: dict,
        level: int,
        lesson_number: int,
        vocab: dict,
    ) -> dict:
        """
        Validate and enhance the generated script.

        Args:
            script: Generated script dictionary
            level: Pimsleur level (1, 2, 3)
            lesson_number: Unit number
            vocab: Vocabulary data

        Returns:
            Enhanced script dictionary
        """
        # Ensure required fields
        script.setdefault("lesson_id", lesson_number)
        script.setdefault("level", level)
        script.setdefault("segments", [])
        script.setdefault("vocabulary_summary", [])

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
            logger.warning("Script may be missing backward build-up (no syllable_practice)")

        if missing_critical:
            logger.warning(f"Script missing critical Pimsleur elements: {missing_critical}")

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
            "expected_native_instructions": lesson_number >= NATIVE_INSTRUCTION_START_UNIT,
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
                "native_model", "model_answer", "context_application",
                "review_in_context", "native_instruction", "grammar_drill"
            ):
                # Native speaker segments
                total += segment.get("duration_estimate", 3)

            elif seg_type in (
                "instruction", "comprehension_question", "prompt_for_composition",
                "prompt_for_question", "repeat_after", "grammar_explanation",
                "cultural_note", "opening_title", "opening_instruction",
                "opening_context", "opening_preview", "recall_question",
                "scenario_setup", "gender_explanation",
                "closing_summary", "closing_instructions"
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
        backward_buildup_sequences = syllable_practice_count // 3  # ~3 syllables per word

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
                segment_types.get("opening_title", 0) > 0 and
                segment_types.get("opening_dialogue", 0) > 0
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
