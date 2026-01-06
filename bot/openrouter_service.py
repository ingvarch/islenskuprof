"""
Module for handling OpenRouter API interactions.
"""
import os
import logging
import re
import time
from typing import List, Tuple, Optional
from openai import OpenAI
from bot.ai_service import AIService
from bot.languages import get_language_config

logger = logging.getLogger(__name__)


class OpenRouterService(AIService):
    """Service for interacting with OpenRouter API."""

    def __init__(self):
        """Initialize OpenRouter client using API key from environment variables."""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")

        self.model = os.environ.get("OPENROUTER_MODEL")
        if not self.model:
            raise ValueError("OPENROUTER_MODEL environment variable is not set")

        # OpenRouter uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # Retry configuration
        self.max_retries = 3
        self.base_delay = 2  # seconds

        logger.info(f"OpenRouter service initialized with model: {self.model}")

    def _call_with_retry(self, messages: List[dict], system_message: str) -> str:
        """
        Make an API call with retry logic.

        Args:
            messages: List of message dicts for the API
            system_message: System message for the model

        Returns:
            str: Generated content

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        for retry in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=4000,
                    messages=[
                        {"role": "system", "content": system_message},
                        *messages
                    ],
                    extra_headers={
                        "HTTP-Referer": os.environ.get("APP_URL", "https://github.com/islenskuprof"),
                        "X-Title": "Islenskuprof Language Learning Bot"
                    }
                )

                content = response.choices[0].message.content
                logger.info(f"Successfully received {len(content)} characters from {self.model}")
                return content

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Check if this is a retryable error
                is_retryable = any(term in error_str for term in [
                    "rate limit", "timeout", "503", "502", "504",
                    "overloaded", "capacity", "temporarily"
                ])

                if is_retryable and retry < self.max_retries - 1:
                    delay = self.base_delay * (2 ** retry)  # Exponential backoff
                    logger.warning(
                        f"Retryable error (attempt {retry + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    continue

                # Not retryable or max retries reached
                logger.error(f"API call failed: {e}")
                raise

        raise last_error

    def generate_icelandic_test(self, prompt: Optional[str] = None) -> str:
        """
        Generate language test content using OpenRouter.

        Args:
            prompt: Custom prompt to use for generation.

        Returns:
            str: Generated test content
        """
        lang_config = get_language_config()

        # Add instruction to mark correct answers
        questions_marker = lang_config.markers.reading_questions
        if prompt and questions_marker.replace("*", "") in prompt:
            prompt += "\n\nIMPORTANT: For all multiple-choice questions, mark the correct answer with (CORRECT) at the end of the option text. For example: 'a) This is the right answer (CORRECT)'."

        logger.info(f"Sending request to OpenRouter to generate {lang_config.name} test content")

        messages = [{"role": "user", "content": prompt}]
        return self._call_with_retry(messages, lang_config.system_message)

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
