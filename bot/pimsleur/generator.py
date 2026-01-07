"""
Pimsleur lesson script generator using LLM.
"""

import json
import logging
from typing import Optional

from bot.openrouter_service import OpenRouterService
from bot.pimsleur.prompts import (
    get_lesson_generation_prompt,
    get_custom_lesson_prompt,
)
from bot.pimsleur.vocabulary_manager import VocabularyProgressionManager
from bot.pimsleur.constants import LESSON_TITLES, VOCABULARY_CURRICULUM

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
            level: CEFR level (A1, A2, B1)
            lesson_number: Lesson number (1-30)
            theme: Optional theme override
            title: Optional title override

        Returns:
            Lesson script dictionary ready for audio generation
        """
        # Get vocabulary for this lesson
        vocab = self.vocab_manager.get_lesson_vocabulary(level, lesson_number)

        # Get theme if not provided
        if not theme:
            theme = self.vocab_manager.get_theme_for_lesson(level, lesson_number)

        # Get title if not provided
        if not title:
            titles = LESSON_TITLES.get(level, [])
            if lesson_number <= len(titles):
                title = titles[lesson_number - 1]
            else:
                title = f"{level} Lesson {lesson_number}: {theme.replace('_', ' ').title()}"

        logger.info(f"Generating script for {level} Lesson {lesson_number}: {title}")

        # Prepare prompts
        system_prompt, user_prompt = get_lesson_generation_prompt(
            target_language=self._language_name,
            lang_code=self._lang_code,
            cefr_level=level,
            lesson_number=lesson_number,
            lesson_title=title,
            theme=theme,
            new_vocabulary=vocab["new"],
            review_vocabulary=vocab["review"],
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
                level=level,
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
        level: str,
        lesson_number: int,
        vocab: dict,
    ) -> dict:
        """
        Validate and enhance the generated script.

        Args:
            script: Generated script dictionary
            level: CEFR level
            lesson_number: Lesson number
            vocab: Vocabulary data

        Returns:
            Enhanced script dictionary
        """
        # Ensure required fields
        script.setdefault("lesson_id", lesson_number)
        script.setdefault("level", level)
        script.setdefault("segments", [])
        script.setdefault("vocabulary_summary", [])

        # Add review lesson references
        review_lessons = self.vocab_manager.get_review_lesson_ids(lesson_number)
        script["review_from_lessons"] = review_lessons

        # Store vocabulary data
        script["vocabulary_new"] = vocab["new"]
        script["vocabulary_review"] = vocab["review"]

        # Calculate actual duration
        script["calculated_duration"] = self._estimate_duration(script)

        # Add segment IDs for tracking
        for i, segment in enumerate(script.get("segments", [])):
            segment["segment_id"] = i

        return script

    def _estimate_duration(self, script: dict) -> int:
        """
        Estimate total duration of script in seconds.

        Args:
            script: Lesson script dictionary

        Returns:
            Estimated duration in seconds
        """
        total = 0
        for segment in script.get("segments", []):
            if segment.get("type") == "pause":
                total += segment.get("duration", 3)
            elif segment.get("type") == "dialogue_segment":
                total += segment.get("duration_estimate", 10)
            else:
                total += segment.get("duration_estimate", 3)
        return total

    def get_script_statistics(self, script: dict) -> dict:
        """
        Get statistics about a generated script.

        Args:
            script: Lesson script dictionary

        Returns:
            Statistics dictionary
        """
        segments = script.get("segments", [])

        segment_types = {}
        for seg in segments:
            seg_type = seg.get("type", "unknown")
            segment_types[seg_type] = segment_types.get(seg_type, 0) + 1

        pause_time = sum(
            seg.get("duration", 0)
            for seg in segments
            if seg.get("type") == "pause"
        )

        return {
            "total_segments": len(segments),
            "segment_types": segment_types,
            "estimated_duration": self._estimate_duration(script),
            "pause_time": pause_time,
            "speaking_time": self._estimate_duration(script) - pause_time,
            "new_vocabulary_count": len(script.get("vocabulary_new", [])),
            "review_vocabulary_count": len(script.get("vocabulary_review", [])),
        }
