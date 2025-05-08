"""
Module for handling Claude AI API interactions.
"""
import os
import logging
import tempfile
import re
import requests
from pathlib import Path
from typing import List, Tuple, Optional
import anthropic
from pydub import AudioSegment
from bot.db.user_service import get_user_audio_speed
from bot.ai_service import AIService

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
        Generate Icelandic language test content using Claude.

        Args:
            prompt: Custom prompt to use for generation. If None, the default prompt will be used.

        Returns:
            str: Generated test content
        """

        # Add instruction to mark correct answers
        if prompt and "Spurningar" in prompt:
            prompt += "\n\nIMPORTANT: For all multiple-choice questions, mark the correct answer with (CORRECT) at the end of the option text. For example: 'a) This is the right answer (CORRECT)'."

        logger.info("Sending request to Claude to generate Icelandic test content")
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system="You are a helpful assistant specialized in creating Icelandic language tests. Always mark the correct answer in multiple-choice questions with (CORRECT).",
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

    def extract_dialogue(self, test_content: str) -> List[Tuple[str, str]]:
        """
        Extract dialogue pairs from the test content.

        Args:
            test_content: The generated test content

        Returns:
            List of tuples containing (speaker, text)
        """
        logger.info("Extracting dialogue from generated test content")
        dialogue_lines = []

        # Use regex to find lines with "Kona:" or "Maður:" (or variations)
        pattern = r'(Kona|Maður|KONA|MAÐUR):\s*(.*?)(?=\n(?:Kona|Maður|KONA|MAÐUR):|$)'
        matches = re.finditer(pattern, test_content, re.DOTALL | re.MULTILINE)

        for match in matches:
            speaker = match.group(1).strip()
            text = match.group(2).strip()
            # Normalize speaker labels
            if speaker.upper() == "KONA":
                speaker = "Kona"
            elif speaker.upper() == "MAÐUR":
                speaker = "Maður"

            dialogue_lines.append((speaker, text))

        logger.info(f"Extracted {len(dialogue_lines)} lines of dialogue")

        # If no dialogue was extracted, return a simple example for testing
        if not dialogue_lines:
            logger.warning("No dialogue was extracted, using fallback example dialogue")
            dialogue_lines = [
                ("Kona", "Heilsugæslan, góðan daginn."),
                ("Maður", "Góðan dag. Ég þarf að breyta tímanum mínum.")
            ]

        return dialogue_lines

    def generate_audio_for_dialogue(self, dialogue_lines: List[Tuple[str, str]], user_id: Optional[int] = None) -> str:
        """
        Generate audio files for each line in the dialogue and merge them into a single file.

        Note: Since Claude doesn't have a native TTS API, we'll use OpenAI's TTS API for audio generation.
        This ensures consistent audio output regardless of which AI provider is used for text generation.

        Args:
            dialogue_lines: List of (speaker, text) tuples
            user_id: Telegram user ID to get audio speed settings (optional)

        Returns:
            Path to the generated audio file
        """
        logger.info(f"Generating audio for {len(dialogue_lines)} dialogue lines using OpenAI TTS API")
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory: {temp_dir}")
        temp_files = []

        # Get user's audio speed if user_id is provided
        user_audio_speed = 1.0  # Default speed
        if user_id:
            user_audio_speed = get_user_audio_speed(user_id)
            logger.info(f"Using audio speed {user_audio_speed} for user {user_id}")

        # Define consistent voice settings for each speaker
        voice_settings = {
            "Kona": {
                "voice": "alloy",
                "speed": user_audio_speed,  # Use user's audio speed
            },
            "Maður": {
                "voice": "onyx",
                "speed": user_audio_speed,  # Use user's audio speed
            }
        }

        try:
            # Initialize OpenAI client for TTS
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set (required for TTS)")

            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_api_key)

            # Generate individual audio files for each line
            for i, (speaker, text) in enumerate(dialogue_lines):
                # Get voice settings based on speaker
                settings = voice_settings.get(speaker, voice_settings["Kona"])
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
                            speed=settings["speed"],  # Add speed parameter
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
