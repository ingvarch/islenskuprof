# Islenskuprof - Icelandic Language Learning Bot

A Telegram bot for learning Icelandic (and German) through AI-generated exercises and Pimsleur-style audio lessons.

## Features

### Learning Modes

**Understanding Section** (`/understanding`)
- AI-generated dialogues with native speaker audio (Listening Comprehension)
- AI-generated reading passages about fictional characters (Reading Comprehension)
- Multiple-choice quiz questions with instant feedback
- Vocabulary, phrases, and grammar notes

**Communication Section** (`/communication`)
- Image-based speaking prompts
- Contextual communication practice

**Pimsleur Lessons** (`/pimsleur`) - NEW
- 30-minute audio lessons following the Pimsleur method
- Spaced repetition (graduated interval recall)
- Anticipation principle: prompt -> pause -> answer -> repeat
- 90 lessons across 3 levels (A1, A2, B1)
- Sequential lesson unlocking (complete N-1 to access N)
- Custom lesson generation from user-provided text

### Personalization

- **Target Language**: Icelandic or German
- **CEFR Level**: A1 through C2 (content adapts to level)
- **Audio Speed**: 0.5x to 2.0x playback
- **Background Effects**: Real-world audio environments (train station, airport, etc.) for advanced listening practice

## Tech Stack

- **Language**: Python 3.13
- **Bot Framework**: python-telegram-bot v20+
- **LLM**: OpenRouter API (OpenAI-compatible)
- **TTS**: VoiceMaker API (neural voices for Icelandic/German)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic

## Requirements

- Python 3.10+
- PostgreSQL database
- ffmpeg (for audio processing)

## Environment Variables

```bash
# Required
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
OPENROUTER_API_KEY="your_openrouter_api_key"
OPENROUTER_MODEL="openai/gpt-4o-mini"  # or other model
VOICEMAKER_API_KEY="your_voicemaker_api_key"
DB_DSN="postgresql://user:password@host:port/database"

# Optional
TARGET_LANGUAGE="is"           # Default target language (is=Icelandic, de=German)
TARGET_LANGUAGES="is,de"       # Languages to seed in database
LOG_LEVEL="info"               # debug, info, warn, error
```

## Setup

1. **Clone and install dependencies:**
```bash
git clone <repository-url>
cd islenskuprof/isl
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. **Set environment variables** (create `.env` file or export)

3. **Run database migrations:**
```bash
python run_migrations.py
```

4. **Start the bot:**
```bash
python main.py
```

## Docker

```bash
docker build -t islenskuprof .
docker run -e TELEGRAM_BOT_TOKEN="..." \
           -e OPENROUTER_API_KEY="..." \
           -e VOICEMAKER_API_KEY="..." \
           -e DB_DSN="..." \
           islenskuprof
```

## Project Structure

```
isl/
├── main.py                     # Entry point
├── bot/
│   ├── telegram_bot.py         # Bot setup and handler registration
│   ├── openrouter_service.py   # LLM API wrapper
│   ├── voicemaker_service.py   # TTS API wrapper
│   ├── ai_service.py           # Abstract AI service base
│   ├── handlers/
│   │   ├── basic_handlers.py       # /start, unknown commands
│   │   ├── section_handlers.py     # /understanding, /communication
│   │   ├── settings_handlers.py    # /settings
│   │   └── pimsleur_handlers.py    # /pimsleur
│   ├── languages/
│   │   ├── base.py             # Abstract LanguageConfig
│   │   ├── icelandic.py        # Icelandic-specific prompts and data
│   │   └── german.py           # German-specific prompts and data
│   ├── pimsleur/               # Pimsleur method module
│   │   ├── generator.py        # Lesson script generation
│   │   ├── audio_assembler.py  # Audio file assembly
│   │   ├── vocabulary_manager.py
│   │   ├── prompts.py          # LLM prompt templates
│   │   └── constants.py        # Curriculum data
│   ├── db/
│   │   ├── database.py         # SQLAlchemy session management
│   │   ├── models.py           # ORM models
│   │   ├── user_service.py     # User CRUD operations
│   │   ├── pimsleur_service.py # Pimsleur lesson operations
│   │   └── seeder.py           # Database seeding
│   └── utils/
│       ├── access_control.py   # Authorization decorators
│       ├── user_tracking.py    # Activity tracking
│       ├── translations.py     # UI translations
│       └── commands.py         # Telegram command registration
├── scripts/
│   └── generate_pimsleur_lessons.py  # CLI for lesson pre-generation
├── alembic/
│   └── versions/               # Database migrations
├── data/                       # Generated audio files
└── requirements.txt
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and settings summary |
| `/understanding` | Listening/Reading comprehension exercises |
| `/communication` | Image-based communication practice |
| `/pimsleur` | Pimsleur-style audio lessons |
| `/settings` | Configure language, level, audio speed, effects |

## Pimsleur Lesson Generation

Pre-generate lessons using the CLI script:

```bash
# Generate a single lesson (script only, for review)
python scripts/generate_pimsleur_lessons.py --level A1 --lesson 1 --script-only

# Generate a lesson with audio
python scripts/generate_pimsleur_lessons.py --level A1 --lesson 1

# Generate a range of lessons
python scripts/generate_pimsleur_lessons.py --level A1 --start 1 --end 10

# Generate all A1 lessons
python scripts/generate_pimsleur_lessons.py --level A1

# Generate all 90 lessons
python scripts/generate_pimsleur_lessons.py --all

# Dry run (see what would be generated)
python scripts/generate_pimsleur_lessons.py --all --dry-run

# Force overwrite existing files without confirmation
python scripts/generate_pimsleur_lessons.py --level A1 --lesson 1 --force
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--lang` | Language code (default: `is` for Icelandic) |
| `--level` | CEFR level: A1, A2, or B1 |
| `--lesson` | Single lesson number (1-30) |
| `--start`, `--end` | Range of lessons to generate |
| `--all` | Generate all 90 lessons |
| `--script-only` | Generate JSON script only, skip audio |
| `--force`, `-f` | Overwrite existing files without asking |
| `--no-db` | Don't save to database |
| `--dry-run` | Show what would be generated |
| `--output` | Output directory (default: `data/pimsleur`) |

## Database Schema

Key tables:
- `users` - Telegram user profiles
- `user_settings` - Preferences (language, level, speed, effects)
- `pimsleur_lessons` - Pre-generated Pimsleur lessons
- `pimsleur_vocabulary` - Vocabulary tracking across lessons
- `user_pimsleur_progress` - User progress through lessons
- `pimsleur_custom_lessons` - User-generated custom lessons

## Voice Configuration

**Icelandic:**
- Female: `ai3-is-IS-Svana`
- Male: `ai3-is-IS-Ulfr`

**German:**
- Female: `pro1-Helena`
- Male: `pro1-Thomas`

**English (narrator for Pimsleur):**
- `ai3-Jony`

## License

MIT
