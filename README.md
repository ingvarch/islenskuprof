# Telegram Bot

A simple Telegram bot built with python-telegram-bot library that generates Icelandic language tests.

## Features

- Responds to `/start` command with a greeting
- Responds to `/help` command with a list of available commands
- Responds to `/section_01` command by generating Icelandic language test content and audio
- Supports Markdown formatting in messages
- Automatically cleans up temporary audio files after sending
- Responds to unknown commands with an appropriate message

## Requirements

- Python 3.7+
- python-telegram-bot library (version 20.0 or higher)
- OpenAI Python library
- pydub library for audio processing

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
   
   # Windows (Command Prompt)
   set TELEGRAM_BOT_TOKEN=your_bot_token_here
   set OPENAI_API_KEY=your_openai_api_key_here
   
   # Windows (PowerShell)
   $env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
   $env:OPENAI_API_KEY="your_openai_api_key_here"
   ```

## Running the Bot

Run the bot with the following command:
```
python main.py
```

The bot will start and listen for commands from users.

## Project Structure

- `main.py`: Entry point for the application
- `bot/`: Package containing the bot implementation
  - `__init__.py`: Package initialization
  - `telegram_bot.py`: Bot implementation with command handlers
  - `openai_service.py`: Service for OpenAI interactions
- `data/`: Directory for generated audio files

## Available Commands

- `/start`: Start interaction with the bot
- `/help`: Show list of available commands
- `/section_01`: Generate Icelandic language test content with audio dialogue
