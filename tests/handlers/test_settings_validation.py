"""
Tests for validation in Settings handlers.
"""

import unittest

from bot.handlers.settings_handlers import (
    LANGUAGE_SELECT_PREFIX,
    AUDIO_SPEED_SELECT_PREFIX,
    LANGUAGE_LEVEL_SELECT_PREFIX,
    TARGET_LANGUAGE_SELECT_PREFIX,
)


class TestSettingsCallbackPrefixes(unittest.TestCase):
    """Test that settings callback prefixes are defined correctly."""

    def test_language_select_prefix_defined(self):
        """Test that language select prefix is defined."""
        self.assertIsInstance(LANGUAGE_SELECT_PREFIX, str)
        self.assertGreater(len(LANGUAGE_SELECT_PREFIX), 0)

    def test_audio_speed_select_prefix_defined(self):
        """Test that audio speed select prefix is defined."""
        self.assertIsInstance(AUDIO_SPEED_SELECT_PREFIX, str)
        self.assertGreater(len(AUDIO_SPEED_SELECT_PREFIX), 0)

    def test_language_level_select_prefix_defined(self):
        """Test that language level select prefix is defined."""
        self.assertIsInstance(LANGUAGE_LEVEL_SELECT_PREFIX, str)
        self.assertGreater(len(LANGUAGE_LEVEL_SELECT_PREFIX), 0)

    def test_target_language_select_prefix_defined(self):
        """Test that target language select prefix is defined."""
        self.assertIsInstance(TARGET_LANGUAGE_SELECT_PREFIX, str)
        self.assertGreater(len(TARGET_LANGUAGE_SELECT_PREFIX), 0)


class TestCallbackDataParsing(unittest.TestCase):
    """Test the callback data parsing logic used in settings handlers."""

    def test_valid_int_parsing(self):
        """Test that valid integer strings parse correctly."""
        test_cases = [
            (f"{LANGUAGE_SELECT_PREFIX}1", 1),
            (f"{LANGUAGE_SELECT_PREFIX}123", 123),
            (f"{AUDIO_SPEED_SELECT_PREFIX}5", 5),
            (f"{LANGUAGE_LEVEL_SELECT_PREFIX}3", 3),
            (f"{TARGET_LANGUAGE_SELECT_PREFIX}42", 42),
        ]

        for callback_data, expected in test_cases:
            prefix = callback_data.split("_")[:-1]
            prefix = "_".join(prefix) + "_"
            value_str = callback_data.replace(prefix, "")
            parsed = int(value_str)
            self.assertEqual(parsed, expected)

    def test_invalid_int_parsing_raises(self):
        """Test that invalid integer strings raise ValueError."""
        invalid_data = [
            f"{LANGUAGE_SELECT_PREFIX}abc",
            f"{LANGUAGE_SELECT_PREFIX}",
            f"{LANGUAGE_SELECT_PREFIX}1.5",
            f"{AUDIO_SPEED_SELECT_PREFIX}not_a_number",
        ]

        for callback_data in invalid_data:
            prefix = callback_data.split("_")[:-1]
            prefix = "_".join(prefix) + "_"
            value_str = callback_data.replace(prefix, "")
            with self.assertRaises(ValueError):
                int(value_str)


class TestPrefixExtraction(unittest.TestCase):
    """Test the prefix extraction logic."""

    def test_language_prefix_extraction(self):
        """Test language ID extraction from callback data."""
        callback_data = f"{LANGUAGE_SELECT_PREFIX}42"
        extracted = callback_data.replace(LANGUAGE_SELECT_PREFIX, "")
        self.assertEqual(extracted, "42")

    def test_audio_speed_prefix_extraction(self):
        """Test audio speed ID extraction from callback data."""
        callback_data = f"{AUDIO_SPEED_SELECT_PREFIX}3"
        extracted = callback_data.replace(AUDIO_SPEED_SELECT_PREFIX, "")
        self.assertEqual(extracted, "3")

    def test_language_level_prefix_extraction(self):
        """Test language level ID extraction from callback data."""
        callback_data = f"{LANGUAGE_LEVEL_SELECT_PREFIX}2"
        extracted = callback_data.replace(LANGUAGE_LEVEL_SELECT_PREFIX, "")
        self.assertEqual(extracted, "2")

    def test_target_language_prefix_extraction(self):
        """Test target language ID extraction from callback data."""
        callback_data = f"{TARGET_LANGUAGE_SELECT_PREFIX}7"
        extracted = callback_data.replace(TARGET_LANGUAGE_SELECT_PREFIX, "")
        self.assertEqual(extracted, "7")


if __name__ == "__main__":
    unittest.main()
