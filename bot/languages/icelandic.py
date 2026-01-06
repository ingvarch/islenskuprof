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
* CRITICAL: The dialogue MUST alternate between {female_label} and {male_label} - both speakers must be present!
* Include 8-10 exchanges in Icelandic (each speaker speaks 4-5 times)
* The dialogue MUST have a natural conclusion - end with a statement (agreement, confirmation, goodbye), NOT a question!
* After the dialogue, add 5 multiple-choice questions (also at {user_language_level} level!)
* VERIFY: Every single word and sentence matches {user_language_level} level before including it

Format the dialogue clearly so I can easily extract it for audio processing.

Your output MUST strictly follow this exact template format:


{markers.story_title} [title of the dialogue]

{markers.listen_instruction}

```
{female_label}: [first line - starts the conversation]
{male_label}: [response]
{female_label}: [continues]
{male_label}: [response]
... (continue alternating)
{female_label} or {male_label}: [FINAL LINE - must be a closing statement like agreement, thanks, or goodbye - NOT a question!]
```

{markers.dialogue_questions}

[Generate 5 TRICKY multiple-choice questions in this EXACT format:

1. [Question text in Icelandic]
a) [Wrong answer - plausible distractor]
b) [Correct answer] (CORRECT)
c) [Wrong answer - uses words from text but wrong meaning]

Rules for tricky questions:
- Q1: Inference question (answer not directly stated)
- Q2: Distractor with words from dialogue but wrong meaning
- Q3: About speaker's intention or emotion
- Q4: Specific detail (time, number, name)
- Q5: What happens next / what they agree on

IMPORTANT: Mark correct answer with (CORRECT) at the end!]

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

=== FINAL CHECKLIST ===
Before submitting, verify you have included ALL these sections:
1. Dialogue with BOTH {female_label} and {male_label} speakers (alternating)
2. 5 multiple-choice questions with (CORRECT) markers
3. KEY VOCABULARY section
4. USEFUL PHRASES section
5. WORD COMBINATIONS section
6. GRAMMAR NOTES section (REQUIRED - do not skip!)
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

[Generate 5 TRICKY multiple-choice questions in this EXACT format:

1. [Question text in Icelandic]
a) [Wrong answer - plausible distractor]
b) [Wrong answer - similar numbers/times/names]
c) [Correct answer] (CORRECT)

Rules for tricky questions:
- Q1: Inference question (not directly stated)
- Q2: Detail with similar numbers/times as distractors
- Q3: WHY question (motivation, not just facts)
- Q4: Paraphrase trap (sounds right but wrong)
- Q5: Feelings, preferences, or future plans

IMPORTANT: Mark correct answer with (CORRECT) at the end!]

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
```

Important: Ensure all words mentioned in GRAMMAR NOTES are first included in the KEY VOCABULARY section.
Include 15-20 items total, prioritizing practical expressions and phrases over single words.
Avoid including very basic words that a {user_language_level} learner would already know.

=== FINAL CHECKLIST ===
Before submitting, verify you have included ALL these sections:
1. Reading passage about the person
2. 5 multiple-choice questions with (CORRECT) markers
3. KEY VOCABULARY section
4. USEFUL PHRASES section
5. WORD COMBINATIONS section
6. GRAMMAR NOTES section (REQUIRED - do not skip!)
"""
