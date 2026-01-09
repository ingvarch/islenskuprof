"""Redis-based persistence for python-telegram-bot."""

import json
import logging
from typing import Any, Optional

from redis.asyncio import Redis
from telegram.ext import BasePersistence, PersistenceInput

logger = logging.getLogger(__name__)


class RedisPersistence(BasePersistence):
    """Redis-based persistence for python-telegram-bot.

    Stores user_data in Redis with automatic expiry.
    Provides state persistence across bot restarts.
    """

    def __init__(
        self, redis_url: str, key_prefix: str = "ptb:", ttl_seconds: int = 86400
    ):
        """Initialize Redis persistence.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            key_prefix: Prefix for all Redis keys
            ttl_seconds: TTL for user data (default 24 hours)
        """
        super().__init__(
            store_data=PersistenceInput(
                bot_data=False,
                chat_data=False,
                user_data=True,
                callback_data=False,
            )
        )
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.ttl_seconds = ttl_seconds
        self._redis: Optional[Redis] = None

    async def _get_redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = Redis.from_url(self.redis_url, decode_responses=True)
            logger.info("Redis connection established")
        return self._redis

    # User data methods (main focus for wizard state)

    async def get_user_data(self) -> dict[int, dict[str, Any]]:
        """Load all user data from Redis."""
        redis = await self._get_redis()
        pattern = f"{self.key_prefix}user:*"
        user_data: dict[int, dict[str, Any]] = {}

        async for key in redis.scan_iter(pattern):
            try:
                user_id = int(key.split(":")[-1])
                data = await redis.get(key)
                if data:
                    user_data[user_id] = json.loads(data)
            except (ValueError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load user data for key {key}: {e}")

        logger.info(f"Loaded user data for {len(user_data)} users from Redis")
        return user_data

    async def update_user_data(self, user_id: int, data: dict[str, Any]) -> None:
        """Save user data to Redis with TTL."""
        redis = await self._get_redis()
        key = f"{self.key_prefix}user:{user_id}"
        await redis.set(key, json.dumps(data), ex=self.ttl_seconds)

    async def drop_user_data(self, user_id: int) -> None:
        """Delete user data from Redis."""
        redis = await self._get_redis()
        key = f"{self.key_prefix}user:{user_id}"
        await redis.delete(key)
        logger.debug(f"Dropped user data for user {user_id}")

    async def refresh_user_data(
        self, user_id: int, user_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Refresh user data from Redis."""
        redis = await self._get_redis()
        key = f"{self.key_prefix}user:{user_id}"
        data = await redis.get(key)
        if data:
            return json.loads(data)
        return user_data

    # Stub methods (not used but required by BasePersistence)

    async def get_bot_data(self) -> dict[str, Any]:
        """Get bot data (not used)."""
        return {}

    async def update_bot_data(self, data: dict[str, Any]) -> None:
        """Update bot data (not used)."""
        pass

    async def refresh_bot_data(self, bot_data: dict[str, Any]) -> dict[str, Any]:
        """Refresh bot data (not used)."""
        return bot_data

    async def get_chat_data(self) -> dict[int, dict[str, Any]]:
        """Get chat data (not used)."""
        return {}

    async def update_chat_data(self, chat_id: int, data: dict[str, Any]) -> None:
        """Update chat data (not used)."""
        pass

    async def drop_chat_data(self, chat_id: int) -> None:
        """Drop chat data (not used)."""
        pass

    async def refresh_chat_data(
        self, chat_id: int, chat_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Refresh chat data (not used)."""
        return chat_data

    async def get_callback_data(self) -> Optional[tuple[list[tuple], dict]]:
        """Get callback data (not used)."""
        return None

    async def update_callback_data(
        self, data: tuple[list[tuple], dict[str, str]]
    ) -> None:
        """Update callback data (not used)."""
        pass

    async def get_conversations(self, name: str) -> dict[tuple, object]:
        """Get conversations (not used)."""
        return {}

    async def update_conversation(
        self, name: str, key: tuple, new_state: Optional[object]
    ) -> None:
        """Update conversation (not used)."""
        pass

    async def flush(self) -> None:
        """Close Redis connection gracefully."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")
