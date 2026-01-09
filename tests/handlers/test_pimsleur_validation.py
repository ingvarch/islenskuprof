"""
Tests for validation in Pimsleur handlers.
"""

import unittest

from bot.handlers.pimsleur_handlers import (
    VALID_FOCUS_VALUES,
    VALID_VOICE_VALUES,
    VALID_DIFFICULTY_VALUES,
)


class TestWizardValidationConstants(unittest.TestCase):
    """Test that wizard validation constants are defined correctly."""

    def test_valid_focus_values_defined(self):
        """Test that focus values are defined."""
        self.assertIsInstance(VALID_FOCUS_VALUES, set)
        self.assertGreater(len(VALID_FOCUS_VALUES), 0)

    def test_valid_focus_values_content(self):
        """Test that focus values contain expected options."""
        expected = {"vocabulary", "pronunciation", "dialogue"}
        self.assertEqual(VALID_FOCUS_VALUES, expected)

    def test_valid_voice_values_defined(self):
        """Test that voice values are defined."""
        self.assertIsInstance(VALID_VOICE_VALUES, set)
        self.assertGreater(len(VALID_VOICE_VALUES), 0)

    def test_valid_voice_values_content(self):
        """Test that voice values contain expected options."""
        expected = {"female", "male", "both"}
        self.assertEqual(VALID_VOICE_VALUES, expected)

    def test_valid_difficulty_values_defined(self):
        """Test that difficulty values are defined."""
        self.assertIsInstance(VALID_DIFFICULTY_VALUES, set)
        self.assertGreater(len(VALID_DIFFICULTY_VALUES), 0)

    def test_valid_difficulty_values_content(self):
        """Test that difficulty values contain expected options."""
        expected = {"1", "2", "3", "auto"}
        self.assertEqual(VALID_DIFFICULTY_VALUES, expected)


class TestValidationLogic(unittest.TestCase):
    """Test the validation logic used in wizard callbacks."""

    def test_focus_validation_accepts_valid(self):
        """Test that valid focus values pass validation."""
        for value in ["vocabulary", "pronunciation", "dialogue"]:
            self.assertIn(value, VALID_FOCUS_VALUES)

    def test_focus_validation_rejects_invalid(self):
        """Test that invalid focus values are rejected."""
        invalid_values = ["invalid", "grammar", "", "VOCABULARY", "123"]
        for value in invalid_values:
            self.assertNotIn(value, VALID_FOCUS_VALUES)

    def test_voice_validation_accepts_valid(self):
        """Test that valid voice values pass validation."""
        for value in ["female", "male", "both"]:
            self.assertIn(value, VALID_VOICE_VALUES)

    def test_voice_validation_rejects_invalid(self):
        """Test that invalid voice values are rejected."""
        invalid_values = ["invalid", "neutral", "", "MALE", "123"]
        for value in invalid_values:
            self.assertNotIn(value, VALID_VOICE_VALUES)

    def test_difficulty_validation_accepts_valid(self):
        """Test that valid difficulty values pass validation."""
        for value in ["1", "2", "3", "auto"]:
            self.assertIn(value, VALID_DIFFICULTY_VALUES)

    def test_difficulty_validation_rejects_invalid(self):
        """Test that invalid difficulty values are rejected."""
        invalid_values = ["0", "4", "easy", "hard", "", "AUTO"]
        for value in invalid_values:
            self.assertNotIn(value, VALID_DIFFICULTY_VALUES)


if __name__ == "__main__":
    unittest.main()
