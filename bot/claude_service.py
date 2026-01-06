"""
Module for handling Claude AI API interactions.
"""
import os
import logging
import re
from typing import List, Tuple, Optional
import anthropic
from bot.ai_service import AIService
from bot.languages import get_language_config

logger = logging.getLogger(__name__)

class ClaudeAIService(AIService):
    """Service for interacting with Claude AI API."""

    def __init__(self):
        """Initialize Claude client using API key from environment variables."""
        api_key = os.environ.get("CLAUDE_API_KEY")
        if not api_key:
            raise ValueError("CLAUDE_API_KEY environment variable is not set")

        model = os.environ.get("CLAUDE_MODEL", "claude-3-7-sonnet-latest")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        logger.info("Claude AI service initialized")

    def generate_icelandic_test(self, prompt: Optional[str] = None) -> str:
        """
        Generate language test content using Claude.

        Args:
            prompt: Custom prompt to use for generation. If None, the default prompt will be used.

        Returns:
            str: Generated test content
        """
        lang_config = get_language_config()

        # Add instruction to mark correct answers
        # Check for questions marker in the configured language
        questions_marker = lang_config.markers.reading_questions
        if prompt and questions_marker.replace("*", "") in prompt:
            prompt += "\n\nIMPORTANT: For all multiple-choice questions, mark the correct answer with (CORRECT) at the end of the option text. For example: 'a) This is the right answer (CORRECT)'."

        logger.info(f"Sending request to Claude to generate {lang_config.name} test content")
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=lang_config.system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.content[0].text
            logger.info(f"Received {len(content)} characters of test content from Claude")
            return content
        except Exception as e:
            logger.error(f"Error generating test content: {e}")
            raise

    def extract_dialogue(self, test_content: str, lang_config=None) -> List[Tuple[str, str]]:
        """
        Extract dialogue pairs from the test content.

        Args:
            test_content: The generated test content
            lang_config: Language configuration (optional, defaults to TARGET_LANGUAGE config)

        Returns:
            List of tuples containing (speaker, text)
        """
        if lang_config is None:
            lang_config = get_language_config()
        logger.info("Extracting dialogue from generated test content")
        dialogue_lines = []

        # Use regex pattern from language config
        pattern = lang_config.dialogue_regex_pattern
        matches = re.finditer(pattern, test_content)

        for match in matches:
            speaker = match.group(1).strip()
            text = match.group(2).strip()
            # Normalize speaker labels using language config
            speaker = lang_config.normalize_speaker(speaker)
            dialogue_lines.append((speaker, text))

        logger.info(f"Extracted {len(dialogue_lines)} lines of dialogue")

        # If no dialogue was extracted, use fallback from language config
        if not dialogue_lines:
            logger.warning("No dialogue was extracted, using fallback example dialogue")
            dialogue_lines = lang_config.get_fallback_dialogue()

        return dialogue_lines

    def generate_audio_for_dialogue(self, dialogue_lines: List[Tuple[str, str]], user_id: Optional[int] = None, lang_config=None) -> str:
        """
        Generate audio files for each line in the dialogue and merge them into a single file.

        Uses VoiceMaker TTS API for audio generation.

        Args:
            dialogue_lines: List of (speaker, text) tuples
            user_id: Telegram user ID to get audio speed settings (optional)
            lang_config: Language configuration (optional, defaults to TARGET_LANGUAGE config)

        Returns:
            Path to the generated audio file
        """
        from bot.voicemaker_service import get_voicemaker_service

        voicemaker = get_voicemaker_service()
        return voicemaker.generate_audio_for_dialogue(dialogue_lines, user_id, lang_config)
