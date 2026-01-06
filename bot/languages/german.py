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
        constraints = self.get_cefr_constraints(user_language_level)

        return f"""
Create a German dialogue for {user_language_level} level learners.
Topic: {topic}

=== CRITICAL {user_language_level} LEVEL REQUIREMENTS ===
- Vocabulary: ONLY use the {constraints['vocabulary_limit']} most common German words
- Sentence length: {constraints['sentence_length']}
- Grammar: {constraints['grammar']}
- Structures: {constraints['structures']}
- Connectors: {constraints['connectors']}
- FORBIDDEN: {constraints['forbidden']}

Example of appropriate {user_language_level} complexity: {constraints['example_complexity']}

=== CONTENT REQUIREMENTS ===
* Create a realistic dialogue between "{female_label}" (woman) and "{male_label}" (man)
* Include 8-10 exchanges in German
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
        constraints = self.get_cefr_constraints(user_language_level)

        return f"""
Write a German reading passage (20-25 sentences) for {user_language_level} level learners.

=== CRITICAL {user_language_level} LEVEL REQUIREMENTS ===
- Vocabulary: ONLY use the {constraints['vocabulary_limit']} most common German words
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
* Write about this person's daily life in Germany
* Use time expressions and daily routine verbs appropriate for {user_language_level}
* After the passage, add 5 multiple-choice questions (also at {user_language_level} level!)
* VERIFY: Every single word and sentence matches {user_language_level} level before including it

Your output MUST strictly follow this exact template format:

*Geschichte uber {person_data["name"]}*

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
