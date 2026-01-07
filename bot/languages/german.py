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
            listen_instruction="*Hören Sie sich dieses Gespräch an.*",
            dialogue_questions="*Fragen zum Gespräch*",
            reading_questions="*Fragen*",
            vocabulary="*Wörterbuch*",
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
* Create a realistic CONVERSATION between TWO people: "{female_label}" (woman) and "{male_label}" (man)
* CRITICAL STRUCTURE:
  - BOTH speakers MUST appear in the dialogue
  - Lines MUST alternate: {female_label} speaks, then {male_label} responds, then {female_label}, etc.
  - Each speaker speaks 4-5 times (total 8-10 lines)
  - The dialogue MUST end with a STATEMENT (agreement, thanks, goodbye), NOT a question!
* After the dialogue, add 5 multiple-choice questions (also at {user_language_level} level!)
* VERIFY: Every word matches {user_language_level} level

=== DIALOGUE STRUCTURE EXAMPLE ===
{female_label}: [Greeting or opening question]
{male_label}: [Response to her]
{female_label}: [Follow-up or new question]
{male_label}: [His response]
{female_label}: [Continues conversation]
{male_label}: [Responds]
... continues alternating ...
{female_label} or {male_label}: [Final statement - agreement, thanks, or goodbye]

Your output MUST follow this exact template format:


{markers.story_title} [title of the dialogue]

{markers.listen_instruction}

```
{female_label}: [starts the conversation]
{male_label}: [responds to her]
{female_label}: [continues]
{male_label}: [responds]
{female_label}: [continues]
{male_label}: [responds]
{female_label}: [continues]
{male_label}: [responds]
{female_label}: [continues]
{male_label}: [FINAL LINE - closing statement, NOT a question]
```

{markers.dialogue_questions}

[Generate 5 TRICKY multiple-choice questions in this EXACT format:

1. [Question text in German]
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

[Generate 5 TRICKY multiple-choice questions in this EXACT format:

1. [Question text in German]
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
