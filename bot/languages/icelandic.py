"""
Icelandic language configuration.
"""
import re
from typing import Dict, List, Tuple, Pattern

from . import register_language
from .base import LanguageConfig, SpeakerConfig, PromptMarkers, SeedData


@register_language("is")
class IcelandicConfig(LanguageConfig):
    """Configuration for Icelandic language learning."""

    @property
    def code(self) -> str:
        return "is"

    @property
    def name(self) -> str:
        return "Icelandic"

    @property
    def native_name(self) -> str:
        return "Islenska"

    @property
    def speakers(self) -> Dict[str, SpeakerConfig]:
        return {
            "female": SpeakerConfig(label="Kona", voice="ai3-is-IS-Svana"),
            "male": SpeakerConfig(label="Madur", voice="ai3-is-IS-Ulfr"),
        }

    @property
    def dialogue_regex_pattern(self) -> Pattern:
        return re.compile(
            r'(Kona|Madur|KONA|MADUR):\s*(.*?)(?=\n(?:Kona|Madur|KONA|MADUR):|$)',
            re.DOTALL | re.MULTILINE
        )

    @property
    def markers(self) -> PromptMarkers:
        return PromptMarkers(
            story_title="*Saga:*",
            listen_instruction="*Hlustadu a thetta samtal.*",
            dialogue_questions="*Spurningar um samtal*",
            reading_questions="*Spurningar*",
            vocabulary="*Ordabok*",
            key_vocabulary="*KEY VOCABULARY:*",
            useful_phrases="*USEFUL PHRASES:*",
            word_combinations="*WORD COMBINATIONS:*",
            grammar_notes="*GRAMMAR NOTES:*",
        )

    @property
    def system_message(self) -> str:
        return (
            "You are a helpful assistant specialized in creating Icelandic language tests. "
            "Always mark the correct answer in multiple-choice questions with (CORRECT)."
        )

    @property
    def seed_data(self) -> SeedData:
        return SeedData(
            names=[
                ("Jon", "Jonsson"),
                ("Anna", "Jonsdottir"),
                ("Olafur", "Sigurdsson"),
                ("Gudrun", "Olafsdottir"),
                ("Einar", "Magnusson"),
                ("Sigridur", "Einarsdottir"),
                ("Magnus", "Thorsson"),
                ("Helga", "Magnusdottir"),
                ("Thor", "Gunnarsson"),
                ("Kristin", "Thorsdottir"),
                ("Gunnar", "Haraldsson"),
                ("Margret", "Gunnarsdottir"),
                ("Harald", "Stefansson"),
                ("Ragnheidur", "Haraldsdottir"),
                ("Stefan", "Bjornsson"),
                ("Hildur", "Stefansdottir"),
                ("Bjorn", "Arnason"),
                ("Ingibjorg", "Bjornsdottir"),
                ("Arni", "Palsson"),
                ("Sigrun", "Arnadottir"),
            ],
            cities=[
                "Reykjavik",
                "Kopavogur",
                "Hafnarfjordur",
                "Akureyri",
                "Gardabaer",
                "Mosfellsbaer",
                "Selfoss",
                "Akranes",
                "Seltjarnarnes",
                "Vestmannaeyjar",
            ],
            jobs=[
                ("laknir", "sjukrahus"),
                ("kennari", "skoli"),
                ("verkfraedingur", "verkfraedistofa"),
                ("hjukrunarfraedingur", "heilsugaesla"),
                ("logfraedingur", "logfraedistofa"),
                ("tolvunarfraedingur", "taknifyrirtaeki"),
                ("bókari", "endurskodunarstofa"),
                ("arkitekt", "arkitektastofa"),
                ("vidhaldsmadur", "fasteignafelag"),
                ("matsveinn", "veitingastaður"),
            ],
            weekend_activities=[
                "fara i golf",
                "hitta vini",
                "fara i sundlaug",
                "lesa bok",
                "horfa a kvikmynd",
                "fara i fjallgongu",
                "heimsaekja fjölskyldu",
                "vinna i gardinum",
                "fara a markad",
                "elda kvöldmat",
            ],
            plan_activities=[
                "fara i matbuð",
                "fara til laeknis",
                "hitta vin",
                "fara i banka",
                "saekja pakka a posthus",
                "skila bókum a bokasafn",
                "fara a fund",
                "saekja börn i skola",
                "fara i thvottahus",
                "borga reikninga",
            ],
            topics=[
                "grocery shopping",
                "visiting the doctor",
                "at the bank",
                "booking a hotel",
                "at the restaurant",
                "public transportation",
                "job interview",
                "renting an apartment",
                "at the pharmacy",
                "making a phone call",
                "at the post office",
                "weather conversation",
                "asking for directions",
                "at the airport",
                "at the library",
            ],
        )

    def detect_gender(self, first_name: str) -> str:
        """Icelandic names ending in 'a' are typically female."""
        return "female" if first_name.lower().endswith('a') else "male"

    def get_fallback_dialogue(self) -> List[Tuple[str, str]]:
        return [
            ("Kona", "Heilsugaeslan, godan daginn."),
            ("Madur", "Godan dag. Eg tharf ad breyta timanum minum."),
        ]

    def get_dialogue_prompt(self, topic: str, user_language: str, user_language_level: str) -> str:
        female_label = self.speakers["female"].label
        male_label = self.speakers["male"].label
        markers = self.markers
        constraints = self.get_cefr_constraints(user_language_level)

        return f"""
Create an Icelandic dialogue for {user_language_level} level learners.
Topic: {topic}

=== CRITICAL {user_language_level} LEVEL REQUIREMENTS ===
- Vocabulary: ONLY use the {constraints['vocabulary_limit']} most common Icelandic words
- Sentence length: {constraints['sentence_length']}
- Grammar: {constraints['grammar']}
- Structures: {constraints['structures']}
- Connectors: {constraints['connectors']}
- FORBIDDEN: {constraints['forbidden']}

Example of appropriate {user_language_level} complexity: {constraints['example_complexity']}

=== CONTENT REQUIREMENTS ===
* Create a realistic dialogue between "{female_label}" (woman) and "{male_label}" (man)
* Include 8-10 exchanges in Icelandic
* After the dialogue, add 5 multiple-choice questions (also at {user_language_level} level!)
* VERIFY: Every single word and sentence matches {user_language_level} level before including it

Format the dialogue clearly so I can easily extract it for audio processing.

Your output MUST strictly follow this exact template format:


{markers.story_title} [title of the dialogue]

{markers.listen_instruction}

```
[dialogue with speakers clearly identified as "{female_label}:" and "{male_label}:"]
```

{markers.dialogue_questions}

[5 TRICKY multiple-choice questions - follow these rules:
- Question 1: Ask about something NOT explicitly stated but can be inferred
- Question 2: Include a distractor answer that uses words from the text but is wrong
- Question 3: Ask about the speaker's intention or emotion, not just facts
- Question 4: Ask about a detail that requires careful reading (time, number, name)
- Question 5: Ask what would likely happen next OR what the speakers agree/disagree on
- All wrong answers should be plausible and use vocabulary from the dialogue
- Avoid obvious wrong answers that are clearly unrelated]

{markers.vocabulary}


{markers.key_vocabulary}

```
* [Word in Icelandic] (grammatical info) - [Translation] - [Part of speech: noun/verb/adjective] in {user_language}]
* [Another key word] (grammatical info) - [Translation] - [Part of speech] in {user_language}]
* thurfa - to need - verb
* [Include all words that will appear in Grammar Notes section]
```


{markers.useful_phrases}

```
* [Phrase in Icelandic] - [Translation to {user_language}] - [Example of how it's used in a sentence in {user_language}]
* [Greeting/Expression] - [Translation] - [When to use this phrase]
```

{markers.word_combinations}

```
* [Common word combination] - [Translation showing how meaning changes in this context]
* [Combination using words from KEY VOCABULARY section] - [Translation and usage example]
```


{markers.grammar_notes}

```
* [Grammatical construction from dialogue] - [Explanation in {user_language}]
* Thurfa + ad + infinitive - expressing necessity (using the verb thurfa from the dictionary)
* [Other grammatical notes using words already listed in KEY VOCABULARY]
```

Important: Ensure all words mentioned in GRAMMAR NOTES are first included in the KEY VOCABULARY section.
Include 15-20 items total, prioritizing practical expressions and phrases over single words.
Avoid including very basic words that a {user_language_level} learner would already know.
```
"""

    def get_reading_prompt(self, person_data: dict, user_language: str, user_language_level: str) -> str:
        markers = self.markers
        constraints = self.get_cefr_constraints(user_language_level)

        return f"""
Write an Icelandic reading passage (20-25 sentences) for {user_language_level} level learners.

=== CRITICAL {user_language_level} LEVEL REQUIREMENTS ===
- Vocabulary: ONLY use the {constraints['vocabulary_limit']} most common Icelandic words
- Sentence length: {constraints['sentence_length']}
- Grammar: {constraints['grammar']}
- Structures: {constraints['structures']}
- Connectors: {constraints['connectors']}
- FORBIDDEN: {constraints['forbidden']}

Example of appropriate {user_language_level} complexity: {constraints['example_complexity']}

=== STORY INFORMATION ===
- Name: {person_data["name"]}
- Gender: {person_data["gender"]}
- Age: {person_data["age"]}
- From: {person_data["origin"]}
- Job: {person_data["job_title"]} at a {person_data["job_workplace"]}
- Children: {person_data["number_of_children"]} children (ages {person_data["age_of_children"]})
- Weekend activity: {person_data["weekend_activity"]}
- Plan for today: {person_data["current_plan"]}

=== CONTENT REQUIREMENTS ===
* Write about this person's daily life in Iceland
* Use time expressions and daily routine verbs appropriate for {user_language_level}
* After the passage, add 5 multiple-choice questions (also at {user_language_level} level!)
* VERIFY: Every single word and sentence matches {user_language_level} level before including it

Your output MUST strictly follow this exact template format:

*Saga um {person_data["name"]}*

```
[passage]
```

{markers.reading_questions}

[5 TRICKY multiple-choice questions - follow these rules:
- Question 1: Ask about something that requires inference (not directly stated)
- Question 2: Ask about a specific detail where wrong answers use similar numbers/times/names
- Question 3: Ask WHY the person does something, not just WHAT they do
- Question 4: Include distractor answers that paraphrase text incorrectly
- Question 5: Ask about the person's feelings, preferences, or future plans
- All wrong answers should be plausible and use vocabulary from the passage
- Never include obviously wrong answers that contradict the text completely]

{markers.vocabulary}


{markers.key_vocabulary}

```
* [Word in Icelandic] (grammatical info) - [Translation] - [Part of speech: noun/verb/adjective] in {user_language}
* [Include all words that will appear in Grammar Notes section]
```


{markers.useful_phrases}

```
* [Phrase in Icelandic] - [Translation to {user_language}] - [Example of how it's used in a sentence in {user_language}]
* [Expression from the passage] - [Translation] - [When to use this phrase]
```


{markers.word_combinations}

```
* [Common word combination from the passage] - [Translation showing how meaning changes in this context]
* [Combination using words from KEY VOCABULARY section] - [Translation and usage example]
```


{markers.grammar_notes}

```
* [Grammatical construction from the passage] - [Explanation in {user_language}]
* [Other grammatical notes using words already listed in KEY VOCABULARY]

Important: Ensure all words mentioned in GRAMMAR NOTES are first included in the KEY VOCABULARY section.
Include 15-20 items total, prioritizing practical expressions and phrases over single words.
Avoid including very basic words that a {user_language_level} learner would already know.
```
"""
