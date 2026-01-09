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

from bot.pimsleur.config import (
    VOICES,
    PAUSE_TRANSITION,
    PAUSE_DIALOGUE,
    PAUSE_SYLLABLE,
    PAUSE_LEARNING,
    SEGMENT_SPEAKER_DEFAULTS,
    LEVEL_SPEED_CONFIG,
    DEFAULT_SPEED_CONFIG,
)

logger = logging.getLogger(__name__)


class PimsleurAudioAssembler:
    """
    Assembles complete Pimsleur lesson audio from script segments.

    Uses VoiceMaker TTS API for speech synthesis and pydub for
    audio processing and merging.
    """

    def __init__(self, language_code: str = "is", level: int = 1):
        """
        Initialize audio assembler.

        Args:
            language_code: ISO language code for native speaker voices
            level: Course level (1, 2, or 3) for progressive speed adjustment
        """
        self.language_code = language_code
        self.level = level
        self.temp_dir: Optional[str] = None

        # Voice mapping based on language
        self.voices = self._get_voices_for_language(language_code)

        # Get speed configuration for this level
        self.speed_config = LEVEL_SPEED_CONFIG.get(level, DEFAULT_SPEED_CONFIG)
        logger.info(
            f"Audio assembler initialized: level={level}, "
            f"speech_speed={self.speed_config['speech_speed']}, "
            f"pause_multiplier={self.speed_config['pause_multiplier']}, "
            f"use_rubberband={self.speed_config['use_rubberband']}"
        )

        # Lazy-load VoiceMaker service
        self._voicemaker = None

        # Check RubberBand availability if needed
        self._rubberband_available = None
        if self.speed_config["use_rubberband"]:
            self._rubberband_available = self._check_rubberband_available()

    @property
    def voicemaker(self):
        """Lazy-load VoiceMaker service."""
        if self._voicemaker is None:
            from bot.voicemaker_service import VoiceMakerService
            self._voicemaker = VoiceMakerService()
        return self._voicemaker

    def _check_rubberband_available(self) -> bool:
        """
        Check if PyRubberBand is available for high-quality time-stretching.

        Returns:
            True if pyrubberband can be imported and used
        """
        try:
            import pyrubberband  # noqa: F401
            import soundfile  # noqa: F401
            logger.info("PyRubberBand available for high-quality time-stretching")
            return True
        except ImportError as e:
            logger.warning(
                f"PyRubberBand not available ({e}), "
                f"falling back to TTS-native speed control"
            )
            return False

    def _apply_time_stretch(self, audio: AudioSegment, rate: float) -> AudioSegment:
        """
        Apply time-stretch to audio using PyRubberBand for natural-sounding speedup.

        Args:
            audio: AudioSegment to stretch
            rate: Stretch rate (1.2 = 20% faster)

        Returns:
            Time-stretched AudioSegment
        """
        if rate == 1.0:
            return audio

        if not self._rubberband_available:
            logger.debug("RubberBand not available, returning original audio")
            return audio

        try:
            import pyrubberband as pyrb
            import soundfile as sf
            import numpy as np

            # Export to temporary WAV for processing
            temp_wav = os.path.join(self.temp_dir, "stretch_temp.wav")
            temp_out = os.path.join(self.temp_dir, "stretch_out.wav")

            # Convert to WAV (pyrubberband needs WAV)
            audio.export(temp_wav, format="wav")

            # Load and stretch
            y, sr = sf.read(temp_wav)
            y_stretched = pyrb.time_stretch(y, sr, rate)

            # Save stretched audio
            sf.write(temp_out, y_stretched, sr)

            # Load back as AudioSegment
            stretched = AudioSegment.from_file(temp_out)

            logger.debug(
                f"Time-stretched audio: {len(audio)}ms -> {len(stretched)}ms "
                f"(rate={rate})"
            )

            # Cleanup temp files
            os.remove(temp_wav)
            os.remove(temp_out)

            return stretched

        except Exception as e:
            logger.error(f"Time-stretch failed: {e}, returning original audio")
            return audio

    def _get_scaled_pause(self, base_pause_ms: int) -> int:
        """
        Apply pause multiplier based on level configuration.

        Args:
            base_pause_ms: Base pause duration in milliseconds

        Returns:
            Scaled pause duration
        """
        multiplier = self.speed_config["pause_multiplier"]
        return int(base_pause_ms * multiplier)

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

        if lang_code == "de":
            voices["native_female"] = VOICES["native_female_de"]
            voices["native_male"] = VOICES["native_male_de"]
        else:
            # Default to Icelandic (covers "is" and any unknown codes)
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

                    # Add appropriate pause between segments based on type
                    if i < total_segments - 1:
                        next_seg = segments[i + 1] if i + 1 < total_segments else None
                        pause_ms = self._get_inter_segment_pause(segment, next_seg)
                        if pause_ms > 0:
                            audio_segments.append(
                                AudioSegment.silent(duration=pause_ms)
                            )

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

    def _get_inter_segment_pause(
        self,
        current_segment: dict,
        next_segment: Optional[dict],
    ) -> int:
        """
        Get pause duration between segments based on context.

        Applies level-based pause scaling for progressive difficulty.

        Args:
            current_segment: Current segment dictionary
            next_segment: Next segment dictionary (if any)

        Returns:
            Pause duration in milliseconds (scaled by level)
        """
        current_type = current_segment.get("type", "")
        next_type = next_segment.get("type", "") if next_segment else ""

        # No pause before explicit pause segments
        if next_type == "pause":
            return 0

        # Syllable practice needs quick transitions
        if current_type == "syllable_practice":
            base_pause = int(PAUSE_SYLLABLE * 200)  # Very short, ~400ms
            return self._get_scaled_pause(base_pause)

        # After native model, short learning pause
        if current_type in ("native_model", "model_answer"):
            base_pause = int(PAUSE_LEARNING * 300)  # ~660ms
            return self._get_scaled_pause(base_pause)

        # After dialogue, slightly longer transition
        if current_type in ("dialogue_segment", "opening_dialogue"):
            base_pause = int(PAUSE_DIALOGUE * 1000)
            return self._get_scaled_pause(base_pause)

        # Default transition pause
        base_pause = int(PAUSE_TRANSITION * 1000)
        return self._get_scaled_pause(base_pause)

    def _generate_segment_audio(
        self,
        segment: dict,
        index: int,
    ) -> Optional[AudioSegment]:
        """
        Generate audio for a single segment.

        Handles all Pimsleur segment types including new backward build-up
        and opening structure segments.

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
            return AudioSegment.silent(duration=int(duration_ms))

        # Handle dialogue segments with multiple lines
        if seg_type in ("dialogue_segment", "opening_dialogue"):
            return self._generate_dialogue_audio(segment, index)

        # All other segments need TTS
        text = segment.get("text", "")
        if not text:
            logger.warning(f"Segment {index} ({seg_type}) has no text, skipping")
            return None

        # Determine speaker from segment or use default for type
        speaker = segment.get("speaker")
        if not speaker:
            speaker = SEGMENT_SPEAKER_DEFAULTS.get(seg_type, "narrator")

        # Resolve language-specific native speakers
        if speaker == "native_female":
            speaker = f"native_female"
        elif speaker == "native_male":
            speaker = f"native_male"

        # Get voice config
        voice_config = self.voices.get(speaker, self.voices["narrator"])

        logger.debug(
            f"Segment {index}: {seg_type}, speaker={speaker}, "
            f"text='{text[:30]}{'...' if len(text) > 30 else ''}'"
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

        Applies level-based speed adjustments:
        - For small speedups (levels 1-2): uses TTS-native speed parameter
        - For larger speedups (level 3+): uses RubberBand post-processing

        Args:
            text: Text to synthesize
            voice_id: VoiceMaker voice ID
            language_code: Language code for TTS
            index: Segment index

        Returns:
            AudioSegment with synthesized speech (speed-adjusted)
        """
        output_file = os.path.join(self.temp_dir, f"segment_{index}.mp3")

        # Determine speed strategy based on configuration
        use_rubberband = self.speed_config["use_rubberband"] and self._rubberband_available
        tts_speed = self.speed_config["speech_speed"]
        stretch_rate = self.speed_config["stretch_rate"]

        # If using RubberBand, generate at normal TTS speed
        # (RubberBand will handle the speedup with better quality)
        if use_rubberband:
            tts_speed = 0

        try:
            audio_data = self.voicemaker._generate_single_audio(
                text=text,
                voice_id=voice_id,
                language_code=language_code,
                speed=tts_speed,
            )

            with open(output_file, "wb") as f:
                f.write(audio_data)

            audio = AudioSegment.from_file(output_file)

            # Apply RubberBand time-stretch if configured
            if use_rubberband and stretch_rate != 1.0:
                audio = self._apply_time_stretch(audio, stretch_rate)

            return audio

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

        Handles both opening_dialogue (teaching foundation) and
        dialogue_segment (practice dialogues).

        Args:
            segment: Dialogue segment dictionary
            index: Segment index

        Returns:
            AudioSegment with complete dialogue
        """
        dialogue = AudioSegment.empty()
        lines = segment.get("lines", [])

        # Pause between dialogue lines (ms) - scaled by level
        base_pause_ms = int(PAUSE_DIALOGUE * 1000)
        line_pause_ms = self._get_scaled_pause(base_pause_ms)

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

            # Add pause between lines (but not after last line)
            if i < len(lines) - 1:
                dialogue += AudioSegment.silent(duration=line_pause_ms)

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
        syllable_count = 0

        for segment in script.get("segments", []):
            seg_type = segment.get("type", "")

            if seg_type == "pause":
                continue

            # Dialogue types have multiple lines
            if seg_type in ("dialogue_segment", "opening_dialogue"):
                for line in segment.get("lines", []):
                    total_chars += len(line.get("text", ""))
                    segments_count += 1
            elif seg_type == "syllable_practice":
                # Syllable segments are typically very short
                text = segment.get("text", "")
                total_chars += len(text)
                segments_count += 1
                syllable_count += 1
            else:
                total_chars += len(segment.get("text", ""))
                segments_count += 1

        # VoiceMaker pricing estimate (neural voices)
        cost_per_char = 0.002  # $0.002 per character
        estimated_cost = total_chars * cost_per_char

        return {
            "total_characters": total_chars,
            "tts_segments": segments_count,
            "syllable_segments": syllable_count,
            "estimated_cost_usd": round(estimated_cost, 2),
        }
