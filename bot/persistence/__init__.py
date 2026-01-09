"""Persistence module for Telegram bot state management."""

from bot.persistence.redis_persistence import RedisPersistence, check_redis_connection

__all__ = ["RedisPersistence", "check_redis_connection"]
