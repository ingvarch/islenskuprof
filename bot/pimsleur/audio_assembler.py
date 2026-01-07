"""
Audio assembler for Pimsleur lessons.

Takes a lesson script JSON and generates a complete audio file
by synthesizing speech for each segment and merging them.
"""

import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from pydub import AudioSegment

from bot.pimsleur.constants import VOICES, PAUSE_BETWEEN_SEGMENTS

logger = logging.getLogger(__name__)


class PimsleurAudioAssembler:
    """
    Assembles complete Pimsleur lesson audio from script segments.

    Uses VoiceMaker TTS API for speech synthesis and pydub for
    audio processing and merging.
    """

    def __init__(self, language_code: str = "is"):
        """
        Initialize audio assembler.

        Args:
            language_code: ISO language code for native speaker voices
        """
        self.language_code = language_code
        self.temp_dir: Optional[str] = None

        # Voice mapping based on language
        self.voices = self._get_voices_for_language(language_code)

        # Lazy-load VoiceMaker service
        self._voicemaker = None

    @property
    def voicemaker(self):
        """Lazy-load VoiceMaker service."""
        if self._voicemaker is None:
            from bot.voicemaker_service import VoiceMakerService
            self._voicemaker = VoiceMakerService()
        return self._voicemaker

    def _get_voices_for_language(self, lang_code: str) -> dict:
        """
        Get voice configuration for a specific language.

        Args:
            lang_code: ISO language code

        Returns:
            Dictionary mapping speaker types to voice configs
        """
        voices = {
            "narrator": VOICES["narrator"],
        }

        if lang_code == "is":
            voices["native_female"] = VOICES["native_female_is"]
            voices["native_male"] = VOICES["native_male_is"]
        elif lang_code == "de":
            voices["native_female"] = VOICES["native_female_de"]
            voices["native_male"] = VOICES["native_male_de"]
        else:
            # Default to Icelandic
            voices["native_female"] = VOICES["native_female_is"]
            voices["native_male"] = VOICES["native_male_is"]

        return voices

    def generate_lesson_audio(
        self,
        script: dict,
        output_path: str,
        progress_callback: Optional[callable] = None,
    ) -> str:
        """
        Generate complete lesson audio from script.

        Args:
            script: Lesson script dictionary with segments
            output_path: Path to save the final audio file
            progress_callback: Optional callback(segment_num, total) for progress

        Returns:
            Path to generated audio file
        """
        self.temp_dir = tempfile.mkdtemp(prefix="pimsleur_")
        logger.info(f"Generating lesson audio, temp dir: {self.temp_dir}")

        segments = script.get("segments", [])
        total_segments = len(segments)
        audio_segments = []

        try:
            for i, segment in enumerate(segments):
                if progress_callback:
                    progress_callback(i + 1, total_segments)

                audio = self._generate_segment_audio(segment, i)
                if audio:
                    audio_segments.append(audio)

                    # Add small pause between segments
                    if i < total_segments - 1:
                        pause = AudioSegment.silent(
                            duration=PAUSE_BETWEEN_SEGMENTS * 1000
                        )
                        audio_segments.append(pause)

            # Merge all segments
            logger.info(f"Merging {len(audio_segments)} audio segments")
            merged = AudioSegment.empty()
            for audio in audio_segments:
                merged += audio

            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # Export final audio
            logger.info(f"Exporting audio to {output_path}")
            merged.export(output_path, format="mp3", bitrate="128k")

            # Log statistics
            duration_sec = len(merged) / 1000
            logger.info(
                f"Generated audio: {duration_sec:.1f}s ({duration_sec/60:.1f} min), "
                f"file size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB"
            )

            return output_path

        finally:
            # Cleanup temp files
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logger.debug(f"Cleaned up temp dir: {self.temp_dir}")

    def _generate_segment_audio(
        self,
        segment: dict,
        index: int,
    ) -> Optional[AudioSegment]:
        """
        Generate audio for a single segment.

        Args:
            segment: Segment dictionary from script
            index: Segment index for temp file naming

        Returns:
            AudioSegment or None for pause segments
        """
        seg_type = segment.get("type")

        # Handle pause segments - just silence
        if seg_type == "pause":
            duration_ms = segment.get("duration", 3) * 1000
            logger.debug(f"Segment {index}: pause {duration_ms}ms")
            return AudioSegment.silent(duration=duration_ms)

        # Handle dialogue segments (multiple lines)
        if seg_type == "dialogue_segment":
            return self._generate_dialogue_audio(segment, index)

        # All other segments need TTS
        text = segment.get("text", "")
        if not text:
            logger.warning(f"Segment {index} has no text, skipping")
            return None

        speaker = segment.get("speaker", "narrator")
        language = segment.get("language", "en")

        # Get voice config
        voice_config = self.voices.get(speaker, self.voices["narrator"])

        logger.debug(
            f"Segment {index}: {seg_type}, speaker={speaker}, "
            f"text='{text[:30]}...'"
        )

        return self._tts_segment(
            text=text,
            voice_id=voice_config["voice_id"],
            language_code=voice_config["language_code"],
            index=index,
        )

    def _tts_segment(
        self,
        text: str,
        voice_id: str,
        language_code: str,
        index: int,
    ) -> AudioSegment:
        """
        Generate TTS audio for a text segment.

        Args:
            text: Text to synthesize
            voice_id: VoiceMaker voice ID
            language_code: Language code for TTS
            index: Segment index

        Returns:
            AudioSegment with synthesized speech
        """
        output_file = os.path.join(self.temp_dir, f"segment_{index}.mp3")

        try:
            audio_data = self.voicemaker._generate_single_audio(
                text=text,
                voice_id=voice_id,
                language_code=language_code,
                speed=0,  # Normal speed for Pimsleur
            )

            with open(output_file, "wb") as f:
                f.write(audio_data)

            return AudioSegment.from_file(output_file)

        except Exception as e:
            logger.error(f"TTS failed for segment {index}: {e}")
            # Return silence as fallback
            estimated_duration = len(text) * 80  # ~80ms per character estimate
            return AudioSegment.silent(duration=max(500, estimated_duration))

    def _generate_dialogue_audio(
        self,
        segment: dict,
        index: int,
    ) -> AudioSegment:
        """
        Generate audio for a dialogue segment with multiple speakers.

        Args:
            segment: Dialogue segment dictionary
            index: Segment index

        Returns:
            AudioSegment with complete dialogue
        """
        dialogue = AudioSegment.empty()
        lines = segment.get("lines", [])

        for i, line in enumerate(lines):
            speaker = line.get("speaker", "native_female")
            text = line.get("text", "")

            if not text:
                continue

            voice_config = self.voices.get(speaker, self.voices["native_female"])

            line_audio = self._tts_segment(
                text=text,
                voice_id=voice_config["voice_id"],
                language_code=voice_config["language_code"],
                index=f"{index}_{i}",
            )

            dialogue += line_audio
            # Short pause between dialogue lines
            dialogue += AudioSegment.silent(duration=500)

        return dialogue

    def estimate_cost(self, script: dict) -> dict:
        """
        Estimate VoiceMaker API cost for generating this script.

        Args:
            script: Lesson script dictionary

        Returns:
            Dictionary with cost estimates
        """
        total_chars = 0
        segments_count = 0

        for segment in script.get("segments", []):
            if segment.get("type") == "pause":
                continue

            if segment.get("type") == "dialogue_segment":
                for line in segment.get("lines", []):
                    total_chars += len(line.get("text", ""))
                    segments_count += 1
            else:
                total_chars += len(segment.get("text", ""))
                segments_count += 1

        # VoiceMaker pricing estimate (neural voices)
        cost_per_char = 0.002  # $0.002 per character
        estimated_cost = total_chars * cost_per_char

        return {
            "total_characters": total_chars,
            "tts_segments": segments_count,
            "estimated_cost_usd": round(estimated_cost, 2),
        }
