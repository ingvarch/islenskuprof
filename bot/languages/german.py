"""
German language configuration.
"""
import re
from typing import Dict, List, Tuple, Pattern

from . import register_language
from .base import LanguageConfig, SpeakerConfig, PromptMarkers, SeedData


@register_language("de")
class GermanConfig(LanguageConfig):
    """Configuration for German language learning."""

    @property
    def code(self) -> str:
        return "de"

    @property
    def name(self) -> str:
        return "German"

    @property
    def native_name(self) -> str:
        return "Deutsch"

    @property
    def speakers(self) -> Dict[str, SpeakerConfig]:
        return {
            "female": SpeakerConfig(label="Frau", voice="pro1-Helena"),
            "male": SpeakerConfig(label="Mann", voice="pro1-Thomas"),
        }

    @property
    def dialogue_regex_pattern(self) -> Pattern:
        return re.compile(
            r'(Frau|Mann|FRAU|MANN):\s*(.*?)(?=\n(?:Frau|Mann|FRAU|MANN):|$)',
            re.DOTALL | re.MULTILINE
        )

    @property
    def markers(self) -> PromptMarkers:
        return PromptMarkers(
            story_title="*Geschichte:*",
            listen_instruction="*Horen Sie sich dieses Gesprach an.*",
            dialogue_questions="*Fragen zum Gesprach*",
            reading_questions="*Fragen*",
            vocabulary="*Worterbuch*",
            key_vocabulary="*KEY VOCABULARY:*",
            useful_phrases="*USEFUL PHRASES:*",
            word_combinations="*WORD COMBINATIONS:*",
            grammar_notes="*GRAMMAR NOTES:*",
        )

    @property
    def system_message(self) -> str:
        return (
            "You are a helpful assistant specialized in creating German language tests. "
            "Always mark the correct answer in multiple-choice questions with (CORRECT)."
        )

    @property
    def seed_data(self) -> SeedData:
        return SeedData(
            names=[
                ("Hans", "Muller"),
                ("Anna", "Schmidt"),
                ("Klaus", "Weber"),
                ("Maria", "Fischer"),
                ("Peter", "Meyer"),
                ("Sabine", "Wagner"),
                ("Thomas", "Becker"),
                ("Monika", "Schulz"),
                ("Michael", "Hoffmann"),
                ("Petra", "Schafer"),
                ("Stefan", "Koch"),
                ("Claudia", "Bauer"),
                ("Andreas", "Richter"),
                ("Karin", "Klein"),
                ("Markus", "Wolf"),
                ("Susanne", "Schroeder"),
                ("Jorg", "Neumann"),
                ("Martina", "Schwarz"),
                ("Frank", "Zimmermann"),
                ("Birgit", "Braun"),
            ],
            cities=[
                "Berlin",
                "Munchen",
                "Hamburg",
                "Koln",
                "Frankfurt",
                "Stuttgart",
                "Dusseldorf",
                "Leipzig",
                "Dortmund",
                "Essen",
            ],
            jobs=[
                ("Arzt", "Krankenhaus"),
                ("Lehrer", "Schule"),
                ("Ingenieur", "Ingenieurburo"),
                ("Krankenschwester", "Klinik"),
                ("Rechtsanwalt", "Kanzlei"),
                ("Informatiker", "IT-Firma"),
                ("Buchhalter", "Wirtschaftsprufung"),
                ("Architekt", "Architekturburo"),
                ("Hausmeister", "Hausverwaltung"),
                ("Koch", "Restaurant"),
            ],
            weekend_activities=[
                "Golf spielen",
                "Freunde treffen",
                "ins Schwimmbad gehen",
                "ein Buch lesen",
                "einen Film schauen",
                "wandern gehen",
                "Familie besuchen",
                "im Garten arbeiten",
                "auf den Markt gehen",
                "Abendessen kochen",
            ],
            plan_activities=[
                "einkaufen gehen",
                "zum Arzt gehen",
                "einen Freund treffen",
                "zur Bank gehen",
                "ein Paket bei der Post abholen",
                "Bucher in die Bibliothek zuruckbringen",
                "zu einer Besprechung gehen",
                "die Kinder von der Schule abholen",
                "in die Wascherei gehen",
                "Rechnungen bezahlen",
            ],
            topics=[
                "Lebensmitteleinkauf",
                "Arztbesuch",
                "bei der Bank",
                "Hotelreservierung",
                "im Restaurant",
                "offentliche Verkehrsmittel",
                "Vorstellungsgesprach",
                "Wohnungsmiete",
                "in der Apotheke",
                "Telefongesprach",
                "bei der Post",
                "Wetter besprechen",
                "nach dem Weg fragen",
                "am Flughafen",
                "in der Bibliothek",
            ],
        )

    def detect_gender(self, first_name: str) -> str:
        """
        Detect gender from German first name using known names and heuristics.
        """
        name_lower = first_name.lower()

        # Explicit female names (don't follow typical endings)
        female_names = {
            'karin', 'birgit', 'ingrid', 'astrid', 'sigrid', 'gudrun',
            'irmgard', 'hildegard', 'gertrud', 'waltraud', 'elfriede',
            'lieselotte', 'hannelore', 'anneliese', 'margot', 'edith',
            'ruth', 'elisabeth', 'doris', 'iris', 'agnes', 'ines',
        }
        if name_lower in female_names:
            return "female"

        # Explicit male names (might match female endings)
        male_names = {
            'andre', 'arne', 'ole', 'janne', 'malte', 'sonne',
            'andreas', 'tobias', 'matthias', 'elias', 'jonas', 'niklas', 'lukas',
            'uwe', 'jens', 'hans', 'klaus', 'peter', 'thomas', 'michael',
            'stefan', 'markus', 'jorg', 'frank', 'ralf', 'bernd', 'dieter',
        }
        if name_lower in male_names:
            return "male"

        # Heuristic: common female endings
        female_endings = ('a', 'e', 'i', 'ie', 'in')
        return "female" if name_lower.endswith(female_endings) else "male"

    def get_fallback_dialogue(self) -> List[Tuple[str, str]]:
        return [
            ("Frau", "Guten Tag, wie kann ich Ihnen helfen?"),
            ("Mann", "Guten Tag. Ich mochte einen Termin vereinbaren."),
        ]

    def get_dialogue_prompt(self, topic: str, user_language: str, user_language_level: str) -> str:
        female_label = self.speakers["female"].label
        male_label = self.speakers["male"].label
        markers = self.markers

        return f"""
Create a German language proficiency test focusing on just ONE dialogue scenario.
IMPORTANT: The topic for this dialogue is: {topic}

STRICTLY follow these guidelines for {user_language_level} level according to CEFR:
* A1: Only use basic phrases, present tense, simple questions. Vocabulary limited to 500 most common words. Only simple sentences (subject-verb-object).
* A2: Simple past tense (Perfekt) allowed, basic conjunctions, vocabulary up to 1000 most common words. Simple sentences with basic connectors.
* B1: Some compound sentences, more verb tenses, vocabulary up to 2000 most common words. Avoid idioms and complex structures.
* B2: Natural flow of conversation, wider range of vocabulary up to 4000 words, some idioms allowed but explained in footnotes.
* C1-C2: No restrictions on vocabulary or grammar complexity.

Listening Section:
* Create a realistic dialogue between two people (a man and a woman) about the chosen everyday topic.
* The dialogue should include 8-10 exchanges and be in German.
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

[5 multiple-choice questions about the dialogue in German]

{markers.vocabulary}


{markers.key_vocabulary}

```
* [Word in German] (grammatical info) - [Translation] - [Part of speech: noun/verb/adjective] in {user_language}]
* [Another key word] (grammatical info) - [Translation] - [Part of speech] in {user_language}]
* brauchen - to need - verb
* [Include all words that will appear in Grammar Notes section]
```


{markers.useful_phrases}

```
* [Phrase in German] - [Translation to {user_language}] - [Example of how it's used in a sentence in {user_language}]
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
* brauchen + zu + Infinitiv - expressing necessity (using the verb brauchen from the dictionary)
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
Write a short German reading comprehension passage - 20-25 sentences long ({user_language_level} CEFR level)
about a person's daily life in Germany.

STRICTLY follow these guidelines for {user_language_level} level according to CEFR:
* A1: Only use basic phrases, present tense, simple questions. Vocabulary limited to 500 most common words. Only simple sentences (subject-verb-object). Sentences should be very short (5-7 words).
* A2: Simple past tense (Perfekt) allowed, basic conjunctions, vocabulary up to 1000 most common words. Simple sentences with basic connectors like "und" (and), "aber" (but), "weil" (because).
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
- Include frequently used German phrases for the level
- Have clear paragraph breaks for readability
- Use sentence length appropriate for the level (shorter for A1-A2, gradually longer for B1-B2)

After the passage, add 5 multiple-choice comprehension questions in German with three answer choices each.
The questions should test understanding of where the person is from, what job they do, what time they wake up,
etc. Ensure that the questions and answer choices also follow the same CEFR level restrictions.

Your output MUST strictly follow this exact template format:

*Geschichte uber {person_data["name"]}*

```
[passage]
```

{markers.reading_questions}

[5 multiple-choice questions about the passage in German]

{markers.vocabulary}


{markers.key_vocabulary}

```
* [Word in German] (grammatical info) - [Translation] - [Part of speech: noun/verb/adjective] in {user_language}
* [Include all words that will appear in Grammar Notes section]
```


{markers.useful_phrases}

```
* [Phrase in German] - [Translation to {user_language}] - [Example of how it's used in a sentence in {user_language}]
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
