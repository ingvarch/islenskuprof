# Telegram Bot

A simple Telegram bot built with python-telegram-bot library that generates Icelandic language tests.

## Features

- Responds to `/start` command with a greeting
- Responds to `/help` command with a list of available commands
- Responds to `/section_01` command by generating Icelandic language test content and audio
- Supports Markdown formatting in messages
- Automatically cleans up temporary audio files after sending
- Responds to unknown commands with an appropriate message
- Stores user information in a PostgreSQL database
- Tracks user interactions with the bot
- Updates user's last contact timestamp whenever they use a command

## Requirements

- Python 3.7+
- python-telegram-bot library (version 20.0 or higher)
- OpenAI Python library
- pydub library for audio processing
- PostgreSQL database
- SQLAlchemy and Alembic for database operations

## Setup

1. Clone this repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a Telegram bot and get your bot token:
   - Talk to [BotFather](https://t.me/botfather) on Telegram
   - Use the `/newbot` command to create a new bot
   - Copy the token provided by BotFather

4. Set the environment variables:
   ```
   # Linux/macOS
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   export OPENAI_API_KEY="your_openai_api_key_here"
   export DB_DSN="postgresql://username:password@hostname:port/database"

   # Windows (Command Prompt)
   set TELEGRAM_BOT_TOKEN=your_bot_token_here
   set OPENAI_API_KEY=your_openai_api_key_here
   set DB_DSN=postgresql://username:password@hostname:port/database

   # Windows (PowerShell)
   $env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
   $env:OPENAI_API_KEY="your_openai_api_key_here"
   $env:DB_DSN="postgresql://username:password@hostname:port/database"
   ```

## Running the Bot

### Database Setup
Before running the bot, you need to set up the database:

1. Make sure PostgreSQL is installed and running
2. Create a database for the bot
3. Set the `DB_DSN` environment variable to point to your database
4. Run the database migrations:
   ```
   ./run_migrations.py upgrade
   ```

### Standard Method
Run the bot with the following command:
```
python main.py
```

The bot will start and listen for commands from users.

### Using Docker
You can also run the bot using Docker:

1. Build the Docker image:
   ```
   docker build -t islenska-citizenship-bot .
   ```

2. Run the Docker container with your environment variables:
   ```
   docker run -e TELEGRAM_BOT_TOKEN="your_bot_token_here" -e OPENAI_API_KEY="your_openai_api_key_here" -e DB_DSN="postgresql://username:password@hostname:port/database" islenska-citizenship-bot
   ```

Note: The Docker image includes ffmpeg, which is required for audio processing.

## Project Structure

- `main.py`: Entry point for the application
- `bot/`: Package containing the bot implementation
  - `__init__.py`: Package initialization
  - `telegram_bot.py`: Bot implementation with command handlers
  - `openai_service.py`: Service for OpenAI interactions
  - `handlers/`: Command handlers for the bot
    - `basic_handlers.py`: Basic command handlers (start, help, etc.)
    - `section_handlers.py`: Section-specific command handlers
  - `utils/`: Utility functions and decorators
    - `access_control.py`: Access control utilities
    - `user_tracking.py`: User tracking utilities
  - `db/`: Database module
    - `__init__.py`: Package initialization
    - `database.py`: Database connection and session management
    - `models.py`: SQLAlchemy models for database tables
    - `user_service.py`: User-related database operations
    - `README.md`: Database module documentation
- `data/`: Directory for generated audio files
- `alembic/`: Database migration scripts
- `alembic.ini`: Alembic configuration file
- `run_migrations.py`: Script to run database migrations

## Available Commands

- `/start`: Start interaction with the bot
- `/help`: Show list of available commands
- `/section_01`: Generate Icelandic language test content with audio dialogue
