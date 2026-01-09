"""
Base classes for language configurations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Tuple, Pattern


@dataclass
class SpeakerConfig:
    """Configuration for a dialogue speaker."""

    label: str  # Display label (e.g., "Kona", "Frau")
    voice: str  # VoiceMaker voice ID (e.g., "ai3-is-IS-Svana", "pro1-Helena")


@dataclass
class PromptMarkers:
    """Markers used in AI-generated content for parsing."""

    story_title: str  # e.g., "*Saga:*"
    listen_instruction: str  # e.g., "*Hlustaðu á þetta samtal.*"
    dialogue_questions: str  # e.g., "*Spurningar um samtal*"
    reading_questions: str  # e.g., "*Spurningar*"
    vocabulary: str  # e.g., "*Orðabók*"
    key_vocabulary: str  # e.g., "*KEY VOCABULARY:*"
    useful_phrases: str  # e.g., "*USEFUL PHRASES:*"
    word_combinations: str  # e.g., "*WORD COMBINATIONS:*"
    grammar_notes: str  # e.g., "*GRAMMAR NOTES:*"


@dataclass
class SeedData:
    """Seed data for database tables."""

    names: List[Tuple[str, str]]  # [(first_name, last_name), ...]
    cities: List[str]  # [city_name, ...]
    jobs: List[Tuple[str, str]]  # [(title, workplace), ...]
    weekend_activities: List[str]  # [activity, ...]
    plan_activities: List[str]  # [activity, ...]
    topics: List[str]  # [topic, ...]


class LanguageConfig(ABC):
    """Abstract base class for language configurations."""

    @property
    @abstractmethod
    def code(self) -> str:
        """ISO 639-1 language code (e.g., 'is', 'de')."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Full language name in English (e.g., 'Icelandic', 'German')."""
        pass

    @property
    @abstractmethod
    def native_name(self) -> str:
        """Language name in the language itself (e.g., 'Íslenska', 'Deutsch')."""
        pass

    @property
    @abstractmethod
    def speakers(self) -> Dict[str, SpeakerConfig]:
        """Speaker configurations keyed by role ('female', 'male')."""
        pass

    @property
    @abstractmethod
    def dialogue_regex_pattern(self) -> Pattern:
        """Compiled regex pattern for extracting dialogue from AI output."""
        pass

    @property
    @abstractmethod
    def markers(self) -> PromptMarkers:
        """Markers for parsing AI-generated content."""
        pass

    @property
    @abstractmethod
    def seed_data(self) -> SeedData:
        """Seed data for populating database tables."""
        pass

    @property
    @abstractmethod
    def system_message(self) -> str:
        """System message for AI chat completions."""
        pass

    @abstractmethod
    def get_dialogue_prompt(
        self, topic: str, user_language: str, user_language_level: str
    ) -> str:
        """
        Generate the prompt for dialogue/listening section.

        Args:
            topic: The topic for the dialogue
            user_language: User's UI language (e.g., 'English', 'Russian')
            user_language_level: CEFR level (e.g., 'A1', 'B2')

        Returns:
            The complete prompt for AI generation
        """
        pass

    @abstractmethod
    def get_reading_prompt(
        self, person_data: dict, user_language: str, user_language_level: str
    ) -> str:
        """
        Generate the prompt for reading comprehension section.

        Args:
            person_data: Dictionary with person information
            user_language: User's UI language (e.g., 'English', 'Russian')
            user_language_level: CEFR level (e.g., 'A1', 'B2')

        Returns:
            The complete prompt for AI generation
        """
        pass

    @abstractmethod
    def detect_gender(self, first_name: str) -> str:
        """
        Detect gender from first name.

        Args:
            first_name: Person's first name

        Returns:
            'female' or 'male'
        """
        pass

    @abstractmethod
    def get_fallback_dialogue(self) -> List[Tuple[str, str]]:
        """
        Return fallback dialogue lines if AI extraction fails.

        Returns:
            List of (speaker_label, text) tuples
        """
        pass

    def normalize_speaker(self, speaker: str) -> str:
        """
        Normalize speaker label to standard form.

        Args:
            speaker: Raw speaker label from AI output

        Returns:
            Normalized speaker label
        """
        speaker_upper = speaker.upper()
        female_label = self.speakers["female"].label
        male_label = self.speakers["male"].label

        if speaker_upper == female_label.upper():
            return female_label
        elif speaker_upper == male_label.upper():
            return male_label
        return speaker

    def get_voice_settings(self, user_audio_speed: float = 1.0) -> Dict[str, Dict]:
        """
        Get voice settings for TTS generation.

        Args:
            user_audio_speed: User's preferred audio speed

        Returns:
            Dict mapping speaker labels to voice settings
        """
        return {
            self.speakers["female"].label: {
                "voice": self.speakers["female"].voice,
                "speed": user_audio_speed,
            },
            self.speakers["male"].label: {
                "voice": self.speakers["male"].voice,
                "speed": user_audio_speed,
            },
        }

    def get_cefr_constraints(self, level: str) -> dict:
        """
        Get detailed CEFR level constraints for content generation.

        Args:
            level: CEFR level (A1, A2, B1, B2, C1, C2)

        Returns:
            Dict with vocabulary, grammar, and sentence constraints
        """
        constraints = {
            "A1": {
                "vocabulary_limit": 500,
                "sentence_length": "5-8 words maximum",
                "grammar": "present tense ONLY, no past tense",
                "structures": "simple subject-verb-object sentences only",
                "connectors": "none or minimal (og/und/and)",
                "forbidden": "NO past tense, NO subjunctive, NO complex clauses, NO idioms",
                "example_complexity": "Ég heiti Anna. Ég bý í Reykjavík. / Ich heiße Anna. Ich wohne in Berlin.",
            },
            "A2": {
                "vocabulary_limit": 1000,
                "sentence_length": "8-12 words maximum",
                "grammar": "present tense, simple past (Perfekt)",
                "structures": "simple sentences with basic connectors",
                "connectors": "og, en, því að, vegna þess / und, aber, weil, denn",
                "forbidden": "NO subjunctive, NO passive voice, NO complex relative clauses, NO idioms",
                "example_complexity": "Ég fór í búð í gær. Ég keypti mjólk og brauð. / Ich bin gestern einkaufen gegangen.",
            },
            "B1": {
                "vocabulary_limit": 2000,
                "sentence_length": "12-18 words",
                "grammar": "all basic tenses, simple conditional",
                "structures": "compound sentences, basic subordinate clauses",
                "connectors": "þegar, ef, áður en, eftir að / wenn, falls, bevor, nachdem",
                "forbidden": "NO rare idioms, NO literary expressions, NO highly specialized vocabulary",
                "example_complexity": "Þegar ég kom heim, var mamma að elda kvöldmat. / Als ich nach Hause kam, kochte meine Mutter.",
            },
            "B2": {
                "vocabulary_limit": 4000,
                "sentence_length": "18-25 words",
                "grammar": "all tenses, passive voice, subjunctive for politeness",
                "structures": "complex sentences, relative clauses",
                "connectors": "full range",
                "forbidden": "NO archaic forms, NO highly specialized jargon",
                "example_complexity": "Natural, flowing conversation with some common idioms explained in footnotes.",
            },
            "C1": {
                "vocabulary_limit": 8000,
                "sentence_length": "no limit",
                "grammar": "full range including subjunctive, all passive forms",
                "structures": "full range of complex structures",
                "connectors": "full range including literary",
                "forbidden": "nothing specific",
                "example_complexity": "Near-native complexity with idioms and nuanced expressions.",
            },
            "C2": {
                "vocabulary_limit": None,
                "sentence_length": "no limit",
                "grammar": "full mastery",
                "structures": "all structures including archaic/literary",
                "connectors": "full range",
                "forbidden": "nothing",
                "example_complexity": "Native-level complexity.",
            },
        }
        return constraints.get(level, constraints["A2"])

    def get_system_message_for_level(self, level: str) -> str:
        """
        Get enhanced system message that enforces CEFR level.

        Args:
            level: CEFR level (A1, A2, B1, B2, C1, C2)

        Returns:
            System message string
        """
        constraints = self.get_cefr_constraints(level)

        return f"""You are an expert {self.name} language teacher creating content for {level} level learners.

CRITICAL REQUIREMENT: All content MUST strictly match {level} CEFR level. This is non-negotiable.

{level} Level Constraints:
- Maximum vocabulary: {constraints["vocabulary_limit"]} most common words
- Sentence length: {constraints["sentence_length"]}
- Grammar allowed: {constraints["grammar"]}
- Sentence structures: {constraints["structures"]}
- Connectors allowed: {constraints["connectors"]}
- FORBIDDEN: {constraints["forbidden"]}

Before generating ANY sentence, verify:
1. Every word is within the {constraints["vocabulary_limit"] or "unlimited"} most common words
2. Grammar matches {level} level requirements
3. Sentence length is appropriate

If you're unsure if a word/structure is appropriate for {level}, use a simpler alternative.

Always mark correct answers in multiple-choice questions with (CORRECT)."""
