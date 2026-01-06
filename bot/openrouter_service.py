"""
Module for handling OpenRouter API interactions with failover support.
"""
import os
import logging
import tempfile
import re
import time
from pathlib import Path
from typing import List, Tuple, Optional
from openai import OpenAI
from pydub import AudioSegment
from bot.db.user_service import get_user_audio_speed
from bot.ai_service import AIService
from bot.languages import get_language_config

logger = logging.getLogger(__name__)

# Default models for failover (in order of preference)
DEFAULT_FAILOVER_MODELS = [
    "anthropic/claude-sonnet-4",
    "openai/gpt-4o",
    "google/gemini-2.0-flash-001",
]


class OpenRouterService(AIService):
    """Service for interacting with OpenRouter API with failover support."""

    def __init__(self):
        """Initialize OpenRouter client using API key from environment variables."""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")

        # Get models from env or use defaults
        models_env = os.environ.get("OPENROUTER_MODELS", "")
        if models_env:
            self.models = [m.strip() for m in models_env.split(",") if m.strip()]
        else:
            self.models = DEFAULT_FAILOVER_MODELS.copy()

        if not self.models:
            raise ValueError("No models configured for OpenRouter failover")

        # OpenRouter uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # Retry configuration
        self.max_retries = 3
        self.base_delay = 2  # seconds

        logger.info(f"OpenRouter service initialized with {len(self.models)} failover models: {self.models}")

    def _call_with_failover(self, messages: List[dict], system_message: str) -> str:
        """
        Make an API call with failover support across multiple models.

        Args:
            messages: List of message dicts for the API
            system_message: System message for the model

        Returns:
            str: Generated content

        Raises:
            Exception: If all models fail after retries
        """
        last_error = None

        for model_index, model in enumerate(self.models):
            logger.info(f"Trying model {model_index + 1}/{len(self.models)}: {model}")

            for retry in range(self.max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=model,
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
                    logger.info(f"Successfully received {len(content)} characters from {model}")
                    return content

                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()

                    # Check if this is a rate limit or temporary error
                    is_retryable = any(term in error_str for term in [
                        "rate limit", "timeout", "503", "502", "504",
                        "overloaded", "capacity", "temporarily"
                    ])

                    if is_retryable and retry < self.max_retries - 1:
                        delay = self.base_delay * (2 ** retry)  # Exponential backoff
                        logger.warning(
                            f"Retryable error on {model} (attempt {retry + 1}/{self.max_retries}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        continue

                    # Not retryable or max retries reached - try next model
                    logger.warning(f"Model {model} failed: {e}. Trying next model...")
                    break

        # All models failed
        logger.error(f"All {len(self.models)} models failed. Last error: {last_error}")
        raise last_error

    def generate_icelandic_test(self, prompt: Optional[str] = None) -> str:
        """
        Generate language test content using OpenRouter with failover.

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
        return self._call_with_failover(messages, lang_config.system_message)

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

        Note: OpenRouter doesn't provide TTS, so we use OpenAI's TTS API for audio generation.

        Args:
            dialogue_lines: List of (speaker, text) tuples
            user_id: Telegram user ID to get audio speed settings (optional)
            lang_config: Language configuration (optional, defaults to TARGET_LANGUAGE config)

        Returns:
            Path to the generated audio file
        """
        if lang_config is None:
            lang_config = get_language_config()
        logger.info(f"Generating audio for {len(dialogue_lines)} dialogue lines using OpenAI TTS API")
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory: {temp_dir}")
        temp_files = []

        # Get user's audio speed if user_id is provided
        user_audio_speed = 1.0  # Default speed
        if user_id:
            user_audio_speed = get_user_audio_speed(user_id)
            logger.info(f"Using audio speed {user_audio_speed} for user {user_id}")

        # Get voice settings from language config
        voice_settings = lang_config.get_voice_settings(user_audio_speed)

        try:
            # Initialize OpenAI client for TTS
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set (required for TTS)")

            openai_client = OpenAI(api_key=openai_api_key)

            # Generate individual audio files for each line
            female_label = lang_config.speakers["female"].label
            for i, (speaker, text) in enumerate(dialogue_lines):
                # Get voice settings based on speaker
                settings = voice_settings.get(speaker, voice_settings[female_label])
                voice = settings["voice"]

                logger.info(f"Generating audio for line {i+1}: {speaker} - '{text[:30]}...' using voice '{voice}'")

                instructions = """
                Voice: Clear, authoritative, and composed, projecting confidence and professionalism.
                Tone: Neutral and informative, maintaining a balance between formality and approachability.
                Punctuation: Structured with commas and pauses for clarity, ensuring information is digestible and well-paced.
                Delivery: Steady and measured, with slight emphasis on key figures and deadlines to highlight critical points.
                """

                file_path = os.path.join(temp_dir, f"part_{i}.mp3")

                # Generate audio with OpenAI with consistent parameters
                try:
                    with openai_client.audio.speech.with_streaming_response.create(
                            model="gpt-4o-mini-tts",
                            voice=voice,
                            speed=settings["speed"],
                            input=text,
                            instructions=instructions,
                            response_format="mp3",
                    ) as response:
                        logger.debug(f"Streaming audio response to file: {file_path}")
                        response.stream_to_file(file_path)

                    logger.debug(f"Audio file created: {file_path}")
                    temp_files.append(file_path)
                except Exception as e:
                    logger.error(f"Error generating audio for line {i+1}: {e}")
                    raise

            # Merge audio files
            logger.info("Merging individual audio files")
            merged_audio = AudioSegment.empty()
            for i, file_path in enumerate(temp_files):
                logger.debug(f"Adding audio file {i+1}/{len(temp_files)} to merged audio")
                audio_segment = AudioSegment.from_file(file_path)
                merged_audio += audio_segment

                # Add a small pause between lines
                pause = AudioSegment.silent(duration=500)  # 500ms pause
                merged_audio += pause

            # Save the merged audio
            output_path = os.path.join(temp_dir, "dialogue.mp3")
            logger.info(f"Exporting merged audio to {output_path}")
            merged_audio.export(output_path, format="mp3")

            # Move to a more permanent location
            final_path = Path(__file__).parent.parent / "data"
            final_path.mkdir(exist_ok=True)
            final_file = final_path / "section_01_dialogue.mp3"

            logger.info(f"Copying audio file to final location: {final_file}")
            # Copy the file to the final location
            with open(output_path, "rb") as src, open(final_file, "wb") as dst:
                dst.write(src.read())

            logger.info(f"Audio generation complete: {final_file}")
            return str(final_file)

        except Exception as e:
            logger.error(f"Error in audio generation process: {e}")
            raise
