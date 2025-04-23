# Database Integration

This module provides PostgreSQL database integration for the Icelandic Citizenship Test Bot.

## Overview

The database module uses SQLAlchemy as an ORM (Object-Relational Mapping) and Alembic for database migrations. It stores user information and tracks user interactions with the bot.

## Configuration

The database connection is configured using the `DB_DSN` environment variable. This should be set to a valid PostgreSQL connection string in the format:

```
postgresql://username:password@hostname:port/database
```

Example:
```
DB_DSN=postgresql://postgres:password@localhost:5432/islenska_bot
```

## Database Schema

### Users Table

The `users` table stores information about Telegram users who interact with the bot:

- `id`: Primary key, auto-incrementing integer
- `telegram_id`: Telegram user ID (unique)
- `username`: Telegram username (optional)
- `first_name`: User's first name (optional)
- `last_name`: User's last name (optional)
- `first_contact`: Timestamp of first interaction with the bot
- `last_contact`: Timestamp of most recent interaction with the bot

## Usage

### User Tracking

The bot automatically tracks user interactions using the `@track_user_activity` decorator. This decorator is applied to all command handlers and updates the user's information in the database whenever they interact with the bot.

### Database Operations

The `user_service.py` module provides functions for common database operations:

- `get_or_create_user`: Get an existing user or create a new one
- `update_user_last_contact`: Update the last_contact timestamp for a user
- `get_user_by_telegram_id`: Get a user by Telegram ID

### Running Migrations

To run database migrations, use the `run_migrations.py` script in the project root:

```bash
# Apply all pending migrations
./run_migrations.py upgrade

# Generate a new migration based on model changes
./run_migrations.py revision

# Rollback the most recent migration
./run_migrations.py downgrade
```

## Development

To add new models or modify existing ones:

1. Update the model definitions in `models.py`
2. Generate a new migration using `./run_migrations.py revision`
3. Apply the migration using `./run_migrations.py upgrade`
