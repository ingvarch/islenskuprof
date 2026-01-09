"""Persistence module for Telegram bot state management."""

from bot.persistence.redis_persistence import RedisPersistence

__all__ = ["RedisPersistence"]
