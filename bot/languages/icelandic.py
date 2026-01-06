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
            "female": SpeakerConfig(label="Kona", voice="alloy"),
            "male": SpeakerConfig(label="Madur", voice="onyx"),
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

        return f"""
Create an Icelandic language proficiency test for citizenship purposes focusing on just ONE dialogue scenario.
IMPORTANT: The topic for this dialogue is: {topic}

STRICTLY follow these guidelines for {user_language_level} level according to CEFR:
* A1: Only use basic phrases, present tense, simple questions. Vocabulary limited to 500 most common words. Only simple sentences (subject-verb-object).
* A2: Simple past tense allowed, basic conjunctions, vocabulary up to 1000 most common words. Simple sentences with basic connectors.
* B1: Some compound sentences, more verb tenses, vocabulary up to 2000 most common words. Avoid idioms and complex structures.
* B2: Natural flow of conversation, wider range of vocabulary up to 4000 words, some idioms allowed but explained in footnotes.
* C1-C2: No restrictions on vocabulary or grammar complexity.

Listening Section:
* Create a realistic dialogue between two people (a man and a woman) about the chosen everyday topic.
* The dialogue should include 8-10 exchanges and be in Icelandic.
* Include common phrases that would be useful in such a setting.
* Clearly identify speakers with labels like "{female_label}:" (Woman) and "{male_label}:" (Man)
* After the dialogue, add 5 multiple-choice questions about details in the conversation.
* Double-check that ALL words and structures in the dialogue strictly match the specified CEFR level.

Format the dialogue clearly so I can easily extract it for audio processing.

Your output MUST strictly follow this exact template format:


{markers.story_title} [title of the dialogue]

{markers.listen_instruction}

```
[dialogue with speakers clearly identified as "{female_label}:" and "{male_label}:"]
```

{markers.dialogue_questions}

[5 multiple-choice questions about the dialogue in Icelandic]

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

        return f"""
Write a short Icelandic reading comprehension passage - 20-25 sentences long ({user_language_level} CEFR level)
about a person's daily life in Iceland.

STRICTLY follow these guidelines for {user_language_level} level according to CEFR:
* A1: Only use basic phrases, present tense, simple questions. Vocabulary limited to 500 most common words. Only simple sentences (subject-verb-object). Sentences should be very short (5-7 words).
* A2: Simple past tense allowed, basic conjunctions, vocabulary up to 1000 most common words. Simple sentences with basic connectors like "og" (and), "en" (but), "thvi" (because).
* B1: Some compound sentences, more verb tenses, vocabulary up to 2000 most common words. Avoid idioms and complex structures.
* B2: Natural flow of text, wider range of vocabulary up to 4000 words, some idioms allowed but explained in footnotes.
* C1-C2: No restrictions on vocabulary or grammar complexity.

Use the following information to guide the story:

- Name: {person_data["name"]}
- Gender: {person_data["gender"]}
- Age: {person_data["age"]}
- From: {person_data["origin"]}
- Job: {person_data["job_title"]} at a {person_data["job_workplace"]}
- Children: {person_data["number_of_children"]} children (ages {person_data["age_of_children"]})
- Usual weekend activity: {person_data["weekend_activity"]}
- Plan for today: {person_data["current_plan"]}

Before writing the passage:
1. Make sure to use time expressions, daily routine verbs, and family-related vocabulary appropriate for the specified level.

The passage should:
- Use vocabulary and grammar structures strictly matching the {user_language_level} level
- Include frequently used Icelandic phrases for the level
- Have clear paragraph breaks for readability
- Use sentence length appropriate for the level (shorter for A1-A2, gradually longer for B1-B2)

After the passage, add 5 multiple-choice comprehension questions in Icelandic with three answer choices each.
The questions should test understanding of where the person is from, what job they do, what time they wake up,
etc. Ensure that the questions and answer choices also follow the same CEFR level restrictions.

Your output MUST strictly follow this exact template format:

*Saga um {person_data["name"]}*

```
[passage]
```

{markers.reading_questions}

[5 multiple-choice questions about the passage in Icelandic]

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
