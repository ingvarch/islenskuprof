"""
Input validator for user-provided text in Pimsleur lessons.

This module provides security validation for user inputs to prevent
prompt injection and other security vulnerabilities.
"""

import re
import logging
from typing import Tuple


class InputValidator:
    """
    Validates and sanitizes user input to prevent security vulnerabilities.

    Uses contextual patterns to detect prompt injection attempts while
    allowing normal vocabulary and phrases for language learning.
    """

    def __init__(self):
        # Patterns that indicate potential prompt injection attempts
        # These are contextual - looking for specific injection phrases, not single words
        self.injection_patterns = [
            # Attempts to override instructions
            r"(?i)ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|commands?)",
            r"(?i)disregard\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|commands?)",
            r"(?i)forget\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|commands?)",
            # Role manipulation
            r"(?i)you\s+are\s+(now\s+)?(a|an|the)\s+(new\s+)?(system|assistant|ai|bot)",
            r"(?i)switch\s+to\s+(a\s+)?(new\s+)?role",
            r"(?i)your\s+(new\s+)?role\s+is",
            # System prompt extraction
            r"(?i)reveal\s+(your\s+)?(system\s+)?prompt",
            r"(?i)show\s+(me\s+)?(your\s+)?(system\s+)?instructions?",
            r"(?i)what\s+(are\s+)?your\s+(system\s+)?instructions?",
            # Output manipulation
            r"(?i)respond\s+(only\s+)?with\s+(the\s+)?(word|text|phrase)",
            r"(?i)output\s+(only|exactly|just)\s+",
            r"(?i)print\s+(only|exactly|just)\s+",
            # Delimiter injection (attempting to close/open new sections)
            r"(?i)\]\s*\[\s*system\s*\]",
            r"(?i)</?(system|user|assistant)>",
            r"(?i)\[/(system|user|assistant)\]",
        ]

        # Logger for security events
        self.logger = logging.getLogger(__name__)

    def validate_text(self, text: str, max_length: int = 10000) -> Tuple[bool, str]:
        """
        Validate user-provided text for security issues.

        Args:
            text: Text to validate
            max_length: Maximum allowed length

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(text, str):
            return False, "Input must be a string"

        # Check length
        if len(text) > max_length:
            return False, f"Input exceeds maximum length of {max_length} characters"

        # Check for empty input
        if not text.strip():
            return False, "Input cannot be empty"

        # Check for injection patterns
        for pattern in self.injection_patterns:
            if re.search(pattern, text):
                self.logger.warning(
                    f"Potential prompt injection detected: pattern matched in text: {text[:100]}..."
                )
                return False, "Input contains potentially unsafe content"

        return True, ""

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text by removing potentially harmful patterns.

        This is a lightweight sanitization that removes only clearly
        malicious patterns while preserving normal text.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        sanitized = text

        # Remove potential delimiter injection attempts
        sanitized = re.sub(r"(?i)</?(system|user|assistant)>", "", sanitized)
        sanitized = re.sub(r"(?i)\[/?(system|user|assistant)\]", "", sanitized)

        return sanitized.strip()

    def validate_vocabulary_item(self, word: str, translation: str) -> Tuple[bool, str]:
        """
        Validate individual vocabulary items.

        Args:
            word: Target language word
            translation: Translation

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate word
        is_valid, error = self.validate_text(word, max_length=100)
        if not is_valid:
            return False, f"Word validation failed: {error}"

        # Validate translation
        is_valid, error = self.validate_text(translation, max_length=200)
        if not is_valid:
            return False, f"Translation validation failed: {error}"

        return True, ""

    def validate_dialogue_line(self, target: str, translation: str) -> Tuple[bool, str]:
        """
        Validate dialogue line components.

        Args:
            target: Target language text
            translation: Translation

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate target language text
        is_valid, error = self.validate_text(target, max_length=500)
        if not is_valid:
            return False, f"Target text validation failed: {error}"

        # Validate translation
        is_valid, error = self.validate_text(translation, max_length=500)
        if not is_valid:
            return False, f"Translation validation failed: {error}"

        return True, ""


# Global validator instance
validator = InputValidator()


def validate_user_input(text: str, max_length: int = 10000) -> Tuple[bool, str]:
    """
    Convenience function to validate user input.

    Args:
        text: Text to validate
        max_length: Maximum allowed length

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validator.validate_text(text, max_length)


def sanitize_user_input(text: str) -> str:
    """
    Convenience function to sanitize user input.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    return validator.sanitize_text(text)
