"""
Module for handling AI API interactions.
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class AIService(ABC):
    """Base class for AI services."""

    @abstractmethod
    def generate_icelandic_test(self, prompt: Optional[str] = None) -> str:
        """
        Generate Icelandic language test content using AI.

        Args:
            prompt: Custom prompt to use for generation. If None, the default prompt will be used.

        Returns:
            str: Generated test content
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
    Factory function to get the appropriate AI service based on environment variables.
    
    Returns:
        AIService: An instance of the appropriate AI service
    """
    ai_provider = os.environ.get("AI_PROVIDER", "OPENAI").upper()
    
    if ai_provider == "OPENAI":
        from bot.openai_service import OpenAIService
        return OpenAIService()
    elif ai_provider == "CLAUDE":
        from bot.claude_service import ClaudeAIService
        return ClaudeAIService()
    else:
        logger.warning(f"Unknown AI provider: {ai_provider}. Falling back to OpenAI.")
        from bot.openai_service import OpenAIService
        return OpenAIService()
