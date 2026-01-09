# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Islenskuprof is a Telegram bot for learning Icelandic and German through AI-generated exercises and Pimsleur-style audio lessons. It combines LLM content generation (OpenRouter API), neural text-to-speech (VoiceMaker API), and spaced repetition methodology.

## Development Commands

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run database migrations
python run_migrations.py

# Start the bot
python main.py

# Pre-generate Pimsleur lessons
python scripts/generate_pimsleur_lessons.py --list              # List available units
python scripts/generate_pimsleur_lessons.py --level 1 --unit 1  # Generate single unit
python scripts/generate_pimsleur_lessons.py --all --dry-run     # Preview all generations
python scripts/generate_pimsleur_lessons.py --level 1 --unit 1 --script-only  # JSON only, no audio

# Docker
docker build -t islenskuprof .
docker run -e TELEGRAM_BOT_TOKEN="..." -e DB_DSN="..." islenskuprof
```

## Quality Checks (run before committing)

```bash
make check          # Run all checks: lint, format, tests
make test           # Run tests only
make fix            # Auto-fix lint issues and format
make clean          # Remove cache files
```

Or manually:
```bash
ruff check --fix .  # Lint and auto-fix issues
ruff format .       # Format code
```

All code changes MUST pass `make check` before committing.

Note: `ruff` is installed in `.venv`, so activate the virtual environment first or use `.venv/bin/ruff`.

## Environment Variables

Required:
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `OPENROUTER_API_KEY` - LLM API key
- `OPENROUTER_MODEL` - Model (e.g., `anthropic/claude-sonnet-4`)
- `VOICEMAKER_API_KEY` - TTS API key
- `DB_DSN` - PostgreSQL connection string

Optional:
- `TARGET_LANGUAGE` - Default language (`is`/`de`, default: `is`)
- `TARGET_LANGUAGES` - Languages to seed (comma-separated)
- `LOG_LEVEL` - debug/info/warn/error
- `ALLOWED_USERS` - Comma-separated Telegram user IDs for access control

## Architecture

### Dependency Flow

```
main.py (entry point)
└── telegram_bot.create_bot()
    └── handlers/ (command/callback routing)
        └── services (OpenRouter, VoiceMaker)
        └── db/ (SQLAlchemy ORM)
            └── PostgreSQL
```

### Key Modules

- `bot/telegram_bot.py` - Bot setup, handler registration
- `bot/openrouter_service.py` - LLM wrapper with retry logic (3 attempts, exponential backoff)
- `bot/voicemaker_service.py` - TTS wrapper
- `bot/handlers/` - Telegram command handlers split by domain
- `bot/pimsleur/` - Pimsleur lesson generation system
- `bot/languages/` - Language-specific configurations (LanguageConfig pattern)
- `bot/db/` - Database layer with session management

### Handler Organization

Handlers split by feature:
- `basic_handlers.py` - `/start`, unknown commands
- `section_handlers.py` - `/understanding`, `/communication`
- `settings_handlers.py` - `/settings` with inline keyboards
- `pimsleur_handlers.py` - `/pimsleur` with wizard UI (WizardState enum for custom lessons)

### Pimsleur System

The Pimsleur module (`bot/pimsleur/`) implements spaced audio lessons:
- `config.py` - Timing constants, voice configs, CEFR guidelines
- `generator.py` - LLM-based lesson script generation
- `audio_assembler.py` - Audio file composition with variable pauses
- `vocabulary_manager.py` - Spaced repetition tracking
- `vocabulary_banks/` - Curated vocabulary per language/level/unit (60+ units)

Key timing constants from `config.py`:
- 30-minute lessons (1800s), 20-minute custom lessons
- Variable pauses by cognitive load (2.0s-6.5s)
- Spaced repetition intervals: 5s, 25s, 2min, 10min, 20min

### Database

PostgreSQL with Alembic migrations in `alembic/versions/`.

Key models (`bot/db/models.py`):
- `User` / `UserSettings` - User profiles and preferences
- `PimsleurLesson` - Stored lesson scripts (JSON)
- `UserPimsleurProgress` - Lesson completion tracking
- `PimsleurCustomLesson` - User-generated lessons

Session pattern: `with db_session() as session:` (context manager in `database.py`)

### Language Configuration

Languages extend `LanguageConfig` base class (`bot/languages/base.py`):
- `icelandic.py` - Icelandic-specific prompts, voices, vocabulary
- `german.py` - German-specific configuration

Selected via `TARGET_LANGUAGE` env var, accessed via `get_language_config()`.

### Access Control

- `@restricted` decorator in `utils/access_control.py` - Whitelist via `ALLOWED_USERS`
- `@track_user_activity` decorator - Activity logging

## Voice Configuration

Icelandic: `ai3-is-IS-Svana` (female), `ai3-is-IS-Ulfr` (male)
German: `pro1-Helena` (female), `pro1-Thomas` (male)
English narrator: `ai3-Jony`

## File Locations

- `data/pimsleur/` - Generated audio files (gitignored)
- `alembic/versions/` - Database migrations
- `bot/pimsleur/vocabulary_banks/` - Curated vocabulary (3 levels x 30 units)

## Clean Code Principles

ALWAYS follow these principles without exception:

- **DRY (Don't Repeat Yourself)**: Extract repeated code into reusable functions, components, or utilities. If you write the same logic twice, refactor immediately.
- **KISS (Keep It Simple, Stupid)**: Choose the simplest solution that works. Avoid clever tricks, unnecessary abstractions, and over-engineering.
- **YAGNI (You Aren't Gonna Need It)**: Never add functionality "just in case". Implement only what is explicitly required right now.

Practical application:
- Before creating a new function/component, check if similar logic already exists
- Prefer composition over inheritance
- Avoid premature optimization and premature abstraction
- Delete dead code immediately, don't comment it out
- One function = one responsibility
- If a function needs a comment to explain what it does, rename it or refactor it

## Input Validation Requirements

When implementing any function that accepts user input (text, files, etc.):

1. **Validate at entry points only** - validate in public API methods, not in internal functions
2. **Use existing validators** - for LLM prompts use `bot/pimsleur/input_validator.py`
3. **Write tests** - every validation function must have unit tests in `tests/`
4. **Contextual patterns** - detect malicious intent, not single words (e.g., block "ignore all previous instructions", not just "ignore")
5. **No HTML escaping for LLM** - don't use `html.escape()` for text going to LLM prompts
