"""
Module for handling AI API interactions.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

class AIService(ABC):
    """Base class for AI services."""

    @abstractmethod
    def generate_content(self, prompt: Optional[str] = None, language_level: str = "A2") -> str:
        """
        Generate language learning content using AI.

        Args:
            prompt: Custom prompt to use for generation.
            language_level: CEFR level (A1, A2, B1, B2, C1, C2) for content difficulty.

        Returns:
            str: Generated content
        """
        pass

    @abstractmethod
    def extract_dialogue(self, test_content: str) -> List[Tuple[str, str]]:
        """
        Extract dialogue pairs from the test content.

        Args:
            test_content: The generated test content

        Returns:
            List of tuples containing (speaker, text)
        """
        pass

    @abstractmethod
    def generate_audio_for_dialogue(self, dialogue_lines: List[Tuple[str, str]], user_id: Optional[int] = None) -> str:
        """
        Generate audio files for each line in the dialogue and merge them into a single file.

        Args:
            dialogue_lines: List of (speaker, text) tuples
            user_id: User ID to get audio speed settings (optional)

        Returns:
            Path to the generated audio file
        """
        pass

def get_ai_service():
    """
    Get the AI service instance.

    Returns:
        AIService: An instance of OpenRouterService
    """
    from bot.openrouter_service import OpenRouterService
    return OpenRouterService()
