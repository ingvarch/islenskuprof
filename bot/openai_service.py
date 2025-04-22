"""
Module for handling OpenAI API interactions.
"""
import os
import logging
import tempfile
import re
from pathlib import Path
from typing import List, Tuple
from openai import OpenAI
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self):
        """Initialize OpenAI client using API key from environment variables."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=api_key)
        logger.info("OpenAI service initialized")
    
    def generate_icelandic_test(self) -> str:
        """
        Generate Icelandic language test content using OpenAI.
        
        Returns:
            str: Generated test content
        """
        prompt = """
        Create an Icelandic language proficiency test for citizenship purposes focusing on just ONE dialogue scenario.
        IMPORTANT: Choose a different topic each time from this list: grocery shopping, at a restaurant, 
        talking about hobbies, discussing the weather, asking for directions, at a clothing store, 
        planning a weekend trip, or meeting someone new. 
    
        Listening Section:
        * Create a realistic dialogue between two people (a man and a woman) about the chosen everyday topic.
        * The dialogue should include 8-10 exchanges and be in Icelandic.
        * Include common phrases that would be useful in such a setting.
        * Clearly identify speakers with labels like "Kona:" (Woman) and "Maður:" (Man)
        * After the dialogue, add 3 multiple-choice questions about details in the conversation.
        * Make sure all sections reflect common vocabulary and sentence structures suitable for A2 level in the CEFR framework.
        Format the dialogue clearly so I can easily extract it for audio processing.
        
        Your output MUST strictly follow this exact template format:
        
        
        *Saga:* [title of the dialogue]

        *Hlustaðu á þetta samtal.*

        ```
        [dialogue with speakers clearly identified as "Kona:" and "Maður:"]
        ```
        
        *Spurningar um samtal*

        [3 multiple-choice questions about the dialogue in Icelandic]
        
        *Orðabók*
        
        ```
        Here is the top-20 hardest word or phrases from the text with translation to Russia
        * [word] - [translation]
        ```
        """

        logger.info("Sending request to OpenAI to generate Icelandic test content")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant specialized in creating Icelandic language tests."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            logger.info(f"Received {len(content)} characters of test content from OpenAI")
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

    def generate_audio_for_dialogue(self, dialogue_lines: List[Tuple[str, str]]) -> str:
        """
        Generate audio files for each line in the dialogue and merge them into a single file.

        Args:
            dialogue_lines: List of (speaker, text) tuples

        Returns:
            Path to the generated audio file
        """
        logger.info(f"Generating audio for {len(dialogue_lines)} dialogue lines")
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory: {temp_dir}")
        temp_files = []

        # Define consistent voice settings for each speaker
        voice_settings = {
            "Kona": {
                "voice": "alloy",
                "speed": 1.0,  # Add consistent speed parameter
            },
            "Maður": {
                "voice": "echo",
                "speed": 1.0,  # Add consistent speed parameter
            }
        }

        try:
            # Generate individual audio files for each line
            for i, (speaker, text) in enumerate(dialogue_lines):
                # Get voice settings based on speaker
                settings = voice_settings.get(speaker, voice_settings["Kona"])
                voice = settings["voice"]

                logger.info(f"Generating audio for line {i+1}: {speaker} - '{text[:30]}...' using voice '{voice}'")

                instructions = """
                Speak in an authentic Icelandic accent. Pronounce words naturally as a native Icelandic speaker would.
                Tone: Clear and conversational, appropriate for an everyday dialogue.
                Speed: Natural conversational pace with appropriate pauses.
                """

                file_path = os.path.join(temp_dir, f"part_{i}.mp3")

                # Generate audio with OpenAI with consistent parameters
                try:
                    with self.client.audio.speech.with_streaming_response.create(
                            model="gpt-4o-mini-tts",
                            voice=voice,
                            speed=settings["speed"],  # Add speed parameter
                            input=text,
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
