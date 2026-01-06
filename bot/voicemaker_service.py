"""
Module for handling VoiceMaker TTS API interactions.
"""
import os
import logging
import tempfile
import time
import requests
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from pydub import AudioSegment
from bot.db.user_service import get_user_audio_speed, get_user_background_effects
from bot.languages import get_language_config

logger = logging.getLogger(__name__)

# VoiceMaker API endpoint
VOICEMAKER_API_URL = "https://developer.voicemaker.in/voice/api"

# Language code mapping for VoiceMaker
LANGUAGE_CODE_MAP = {
    "is": "is-IS",  # Icelandic
    "de": "de-DE",  # German
    "en": "en-US",  # English (default)
}

# Engine mapping based on voice prefix
ENGINE_MAP = {
    "ai3": "neural",
    "ai2": "neural",
    "pro1": "neural",
    "standard": "standard",
}

# VoxFX preset mapping by CEFR level
# Lower levels = cleaner audio, higher levels = more challenging listening conditions
VOXFX_PRESETS_BY_LEVEL = {
    "A1": None,  # No effects - clear audio for beginners
    "A2": None,  # No effects - clear audio for elementary
    "B1": {
        "presetId": "67841788096cecfe8b18b2d5",  # Train Station
        "dryWet": 30,  # Light effect
    },
    "B2": {
        "presetId": "67841788096cecfe8b18b2d3",  # Airport Announcement
        "dryWet": 50,  # Medium effect
    },
    "C1": {
        "presetId": "67841788096cecfe8b18b2d7",  # Subway Train Inside
        "dryWet": 60,  # Stronger effect
    },
    "C2": {
        "presetId": "67841788096cecfe8b18b2f7",  # Poor Signal
        "dryWet": 70,  # Challenging listening conditions
    },
}


class VoiceMakerService:
    """Service for generating TTS audio using VoiceMaker API."""

    def __init__(self):
        """Initialize VoiceMaker client using API key from environment variables."""
        self.api_key = os.environ.get("VOICEMAKER_API_KEY")
        if not self.api_key:
            raise ValueError("VOICEMAKER_API_KEY environment variable is not set")

        # Retry configuration
        self.max_retries = 3
        self.base_delay = 2  # seconds

        logger.info("VoiceMaker TTS service initialized")

    def _get_engine_from_voice(self, voice_id: str) -> str:
        """Determine the engine type from voice ID prefix."""
        for prefix, engine in ENGINE_MAP.items():
            if voice_id.startswith(prefix):
                return engine
        return "neural"  # default

    def _generate_single_audio(
        self,
        text: str,
        voice_id: str,
        language_code: str,
        speed: int = 0,
        voxfx: Optional[Dict] = None,
    ) -> bytes:
        """
        Generate audio for a single text using VoiceMaker API.

        Args:
            text: Text to convert to speech
            voice_id: VoiceMaker voice ID (e.g., "ai3-is-IS-Svana")
            language_code: Language code (e.g., "is-IS")
            speed: Speed adjustment (-100 to 100), default 0
            voxfx: Optional VoxFX preset configuration for background effects

        Returns:
            Audio data as bytes

        Raises:
            Exception: If API call fails after retries
        """
        engine = self._get_engine_from_voice(voice_id)

        payload = {
            "Engine": engine,
            "VoiceId": voice_id,
            "LanguageCode": language_code,
            "Text": text,
            "OutputFormat": "mp3",
            "SampleRate": "48000",
            "Effect": "default",
            "MasterVolume": "0",
            "MasterSpeed": str(speed),
            "MasterPitch": "0",
        }

        # Add VoxFX effects if provided
        if voxfx:
            payload["VoxFx"] = voxfx
            logger.debug(f"Applying VoxFX preset: {voxfx['presetId']} with dryWet: {voxfx['dryWet']}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error = None
        for retry in range(self.max_retries):
            try:
                logger.debug(f"Sending TTS request to VoiceMaker: voice={voice_id}, text='{text[:50]}...'")

                response = requests.post(
                    VOICEMAKER_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=60,
                )

                response.raise_for_status()
                result = response.json()

                if not result.get("success"):
                    error_msg = result.get("message", "Unknown error")
                    raise Exception(f"VoiceMaker API error: {error_msg}")

                # Download the audio file
                audio_url = result.get("path")
                if not audio_url:
                    raise Exception("VoiceMaker API did not return audio URL")

                logger.debug(f"Downloading audio from: {audio_url}")
                audio_response = requests.get(audio_url, timeout=60)
                audio_response.raise_for_status()

                logger.debug(f"Successfully generated {len(audio_response.content)} bytes of audio")
                return audio_response.content

            except requests.exceptions.RequestException as e:
                last_error = e
                if retry < self.max_retries - 1:
                    delay = self.base_delay * (2 ** retry)
                    logger.warning(
                        f"VoiceMaker request failed (attempt {retry + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    continue
                raise

            except Exception as e:
                last_error = e
                logger.error(f"VoiceMaker API error: {e}")
                raise

        raise last_error

    def generate_audio_for_dialogue(
        self,
        dialogue_lines: List[Tuple[str, str]],
        user_id: Optional[int] = None,
        lang_config=None,
        language_level: str = "A2",
    ) -> str:
        """
        Generate audio files for each line in the dialogue and merge them into a single file.

        Args:
            dialogue_lines: List of (speaker, text) tuples
            user_id: Telegram user ID to get audio speed settings (optional)
            lang_config: Language configuration (optional, defaults to TARGET_LANGUAGE config)
            language_level: CEFR language level for VoxFX effects (default: A2)

        Returns:
            Path to the generated audio file
        """
        if lang_config is None:
            lang_config = get_language_config()

        logger.info(f"Generating audio for {len(dialogue_lines)} dialogue lines using VoiceMaker")
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory: {temp_dir}")
        temp_files = []

        # Get user's audio speed if user_id is provided
        user_audio_speed = 1.0  # Default speed
        background_effects_enabled = False
        if user_id:
            user_audio_speed = get_user_audio_speed(user_id)
            background_effects_enabled = get_user_background_effects(user_id)
            logger.info(f"Using audio speed {user_audio_speed} for user {user_id}")
            logger.info(f"Background effects enabled: {background_effects_enabled}")

        # Get VoxFX preset based on language level (only if enabled)
        voxfx_preset = None
        if background_effects_enabled:
            voxfx_preset = VOXFX_PRESETS_BY_LEVEL.get(language_level)
            if voxfx_preset:
                logger.info(f"Using VoxFX preset for {language_level} level: {voxfx_preset['presetId']}")
            else:
                logger.info(f"No VoxFX preset for {language_level} level (clean audio)")

        # Convert speed to VoiceMaker format (-100 to 100)
        # user_audio_speed is typically 0.5 to 2.0, where 1.0 is normal
        # VoiceMaker uses -100 (slowest) to 100 (fastest), 0 is normal
        voicemaker_speed = int((user_audio_speed - 1.0) * 100)
        voicemaker_speed = max(-100, min(100, voicemaker_speed))  # Clamp to valid range

        # Get voice settings from language config
        voice_settings = lang_config.get_voice_settings(user_audio_speed)

        # Get language code for VoiceMaker
        language_code = LANGUAGE_CODE_MAP.get(lang_config.code, "en-US")

        try:
            # Generate individual audio files for each line
            female_label = lang_config.speakers["female"].label
            for i, (speaker, text) in enumerate(dialogue_lines):
                # Get voice settings based on speaker
                settings = voice_settings.get(speaker, voice_settings[female_label])
                voice_id = settings["voice"]

                logger.info(f"Generating audio for line {i+1}: {speaker} - '{text[:30]}...' using voice '{voice_id}'")

                file_path = os.path.join(temp_dir, f"part_{i}.mp3")

                try:
                    audio_data = self._generate_single_audio(
                        text=text,
                        voice_id=voice_id,
                        language_code=language_code,
                        speed=voicemaker_speed,
                        voxfx=voxfx_preset,
                    )

                    with open(file_path, "wb") as f:
                        f.write(audio_data)

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
            with open(output_path, "rb") as src, open(final_file, "wb") as dst:
                dst.write(src.read())

            logger.info(f"Audio generation complete: {final_file}")
            return str(final_file)

        except Exception as e:
            logger.error(f"Error in audio generation process: {e}")
            raise


# Singleton instance
_voicemaker_service: Optional[VoiceMakerService] = None


def get_voicemaker_service() -> VoiceMakerService:
    """Get or create the VoiceMaker service singleton."""
    global _voicemaker_service
    if _voicemaker_service is None:
        _voicemaker_service = VoiceMakerService()
    return _voicemaker_service
