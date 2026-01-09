# Spaced Audio Course Generator

Audio lesson generator based on spaced repetition methodology. Generates structured lessons with vocabulary progression, backward build-up technique, and comprehension exercises.

## Directory Structure

```
bot/pimsleur/
├── config.py                 # Configuration, CEFR guidelines, brand settings
├── generator.py              # Main lesson generator
├── prompts.py                # LLM prompts for script generation
├── vocabulary_manager.py     # Vocabulary progression management
├── audio_assembler.py        # Audio file assembly
├── languages/                # Legacy language modules (deprecated)
│   └── icelandic/
│       └── level_01_*.py     # Old unit files
└── vocabulary_banks/         # New vocabulary bank system
    ├── __init__.py           # VocabularyBank class
    ├── fallback_prompts.py   # CEFR-guided LLM generation
    └── icelandic/
        ├── categories.py     # 90 unit themes
        ├── level_01/         # Level 1 (A1-A2) vocabulary
        ├── level_02/         # Level 2 (A2-B1) vocabulary
        └── level_03/         # Level 3 (B1-B2) vocabulary
```

## CEFR Level Mapping

| Level | CEFR | Name | Target Words | Description |
|-------|------|------|--------------|-------------|
| 1 | A1-A2 | Beginner | 500 | Survival vocabulary |
| 2 | A2-B1 | Intermediate | 500 | Conversational vocabulary |
| 3 | B1-B2 | Upper Intermediate | 500 | Fluent vocabulary |

## Hybrid Vocabulary System

The generator uses a hybrid approach:

1. **Bank files** (priority): Curated vocabulary files in `vocabulary_banks/<language>/level_XX/`
2. **LLM fallback**: CEFR-guided generation when no bank data exists

This ensures lessons can be generated for any unit while allowing curated content where available.

## Adding Vocabulary

### Step 1: Create Unit File

Create a file in the appropriate level directory:

```
bot/pimsleur/vocabulary_banks/icelandic/level_01/unit_05.py
```

### Step 2: Use Standard Format

```python
"""
Icelandic Level 1, Unit 5: "Where Are You From?"

Vocabulary format: (icelandic, english, type, pronunciation)
"""

UNIT_INFO = {
    "unit": 5,
    "level": 1,
    "title": "Where Are You From?",
    "categories": ["personal_info", "nationalities", "countries"],
}

# Opening dialogue - conversation that introduces vocabulary naturally
OPENING_DIALOGUE = [
    ("Hvadan ertu?", "Where are you from?"),
    ("Eg er fra Bandarikjunum.", "I'm from the United States."),
    ("Ertu islenskur?", "Are you Icelandic?"),
    ("Nei, eg er bandariskur.", "No, I'm American."),
]

# New vocabulary: 15-20 words per unit
# Format: (target_word, translation, word_type, phonetic)
VOCABULARY = [
    ("hvadan", "where from", "question_word", "KVA-than"),
    ("fra", "from", "preposition", "frow"),
    ("land", "country", "noun", "LAHND"),
    ("Bandarikjunum", "United States", "noun", "BAN-da-REEK-yu-num"),
    ("islenskur", "Icelandic (m)", "adjective", "EES-len-skur"),
    ("islensk", "Icelandic (f)", "adjective", "EES-lensk"),
    # ... more words
]

# Key phrases: 4-6 expressions using vocabulary
PHRASES = [
    ("Hvadan ertu?", "Where are you from?", "asking origin"),
    ("Eg er fra...", "I'm from...", "stating origin"),
]

# Grammar notes: 3-5 relevant points
GRAMMAR_NOTES = [
    "Preposition 'fra' takes dative case",
    "Country names often end in '-land'",
    "Adjective gender: islenskur (m) / islensk (f)",
]

# Units to review vocabulary from (spaced repetition)
REVIEW_FROM_UNITS = [1, 2, 3, 4]
```

### Word Types

Use these standardized word types:

| Category | Types |
|----------|-------|
| Nouns | `noun`, `noun_plural`, `noun_genitive`, `noun_dative` |
| Verbs | `verb`, `verb_past`, `verb_participle` |
| Adjectives | `adjective`, `adjective_feminine`, `adjective_neuter` |
| Others | `adverb`, `preposition`, `conjunction`, `pronoun` |
| Questions | `question_word`, `interjection` |
| Phrases | `phrase`, `expression`, `greeting` |

### Pronunciation Guide Format

Use English-approximation phonetics:

- Capital letters = stressed syllable
- Use familiar English sounds
- Examples:
  - "afsakid" -> "AHF-sa-kith"
  - "skilur" -> "SKI-lur"
  - "thu" -> "thoo"
  - "eg" -> "yeh"

## Unit Themes

All 90 units have predefined themes in `vocabulary_banks/icelandic/categories.py`:

```python
# Level 1 examples
1: ("survival_skills", "Excuse Me, Do You Understand?"),
2: ("meet_greet", "Hello, How Are You?"),
3: ("nationalities", "Are You Icelandic?"),
...

# Level 2 examples
1: ("directions_complex", "Finding Your Way"),
2: ("transactions", "At the Bank"),
...

# Level 3 examples
1: ("hypotheticals", "If I Were..."),
2: ("subjunctive", "I Wish That..."),
```

## Generating Lessons

### Generate Single Unit

```bash
# Script only (no audio)
python scripts/generate_pimsleur_lessons.py --level 1 --unit 5 --script-only

# With audio
python scripts/generate_pimsleur_lessons.py --level 1 --unit 5

# Force regeneration
python scripts/generate_pimsleur_lessons.py --level 1 --unit 5 --force
```

### Generate Range

```bash
# Generate Level 1, Units 1-10
python scripts/generate_pimsleur_lessons.py --level 1 --start 1 --end 10 --script-only
```

### Output

Scripts are saved to:
```
data/pimsleur/is/level_01/is_L01_U05_script.json
data/pimsleur/is/level_01/is_L01_U05_audio.mp3
```

## Opening/Closing Format

Lessons use trademark-safe branding:

**Opening:**
```
"This is Level 1, Unit 5 of your Icelandic Spaced Audio Course."
```

**Closing:**
```
"This is the end of Level 1, Unit 5."
```

## Adding a New Language

1. Create language directory:
   ```
   bot/pimsleur/vocabulary_banks/<language_code>/
   ```

2. Create `categories.py` with 90 unit themes

3. Create level directories:
   ```
   level_01/
   level_02/
   level_03/
   ```

4. Add unit files using the standard format

5. Update `VocabularyBank` class if needed

## LLM Fallback Quality

When no bank data exists, the LLM generates vocabulary following CEFR guidelines:

**A1 (Level 1, early units):**
- Concrete nouns (food, objects, places)
- Basic verbs (be, have, want, go)
- Numbers 1-100
- Simple question words

**A2 (Level 1, later units):**
- Past tense markers
- Comparative adjectives
- Basic connectors (because, but)

**B1 (Level 2):**
- Conditional structures
- Modal verbs (could, should)
- Abstract nouns
- Common idioms

**B2 (Level 3):**
- Hypothetical language
- Formal/informal register
- Advanced idioms
- Complex sentence structures

## Testing

```bash
# Test VocabularyBank
python -c "
from bot.pimsleur.vocabulary_banks import VocabularyBank
bank = VocabularyBank('is')
data = bank.get_unit(1, 1)
print(f'Words: {len(data.get(\"vocabulary\", []))}')
print(f'Source: {data.get(\"source\", \"bank\")}')
"

# Test theme lookup
python -c "
from bot.pimsleur.vocabulary_banks.icelandic.categories import get_unit_theme
theme, title = get_unit_theme(2, 15)
print(f'Theme: {theme}, Title: {title}')
"
```
