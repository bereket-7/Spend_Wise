"""Redis cache utilities with graceful fallback when Redis is unavailable."""
import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

_redis_client = None
_redis_checked = False


def _cache_enabled() -> bool:
    return os.getenv('CACHE_ENABLED', 'true').lower() in ('1', 'true', 'yes')


def _get_redis():
    """Lazy-initialize Redis client; return None if unavailable."""
    global _redis_client, _redis_checked
    if not _cache_enabled():
        return None
    if _redis_checked:
        return _redis_client

    _redis_checked = True
    try:
        import redis

        url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        client = redis.from_url(url, decode_responses=True, socket_connect_timeout=1)
        client.ping()
        _redis_client = client
        logger.info("Redis cache connected")
    except Exception as e:
        logger.warning(f"Redis unavailable, caching disabled: {e}")
        _redis_client = None
    return _redis_client


def cache_get(key: str) -> Optional[str]:
    """Get a string value from cache."""
    client = _get_redis()
    if not client:
        return None
    try:
        return client.get(key)
    except Exception as e:
        logger.warning(f"cache_get failed for {key}: {e}")
        return None


def cache_get_json(key: str) -> Optional[Any]:
    """Get and deserialize a JSON value from cache."""
    raw = cache_get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def cache_set(key: str, value: str, ttl_seconds: int = 300) -> bool:
    """Set a string value in cache with TTL."""
    client = _get_redis()
    if not client:
        return False
    try:
        client.setex(key, ttl_seconds, value)
        return True
    except Exception as e:
        logger.warning(f"cache_set failed for {key}: {e}")
        return False


def cache_set_json(key: str, value: Any, ttl_seconds: int = 300) -> bool:
    """Serialize and set a JSON value in cache."""
    try:
        return cache_set(key, json.dumps(value), ttl_seconds)
    except (TypeError, ValueError) as e:
        logger.warning(f"cache_set_json serialize failed: {e}")
        return False


def cache_delete_pattern(prefix: str) -> int:
    """Delete all keys matching prefix*."""
    client = _get_redis()
    if not client:
        return 0
    try:
        deleted = 0
        for key in client.scan_iter(match=f"{prefix}*"):
            client.delete(key)
            deleted += 1
        return deleted
    except Exception as e:
        logger.warning(f"cache_delete_pattern failed for {prefix}: {e}")
        return 0


def invalidate_user_cache(user_id: int) -> None:
    """Invalidate all cached smart-feature data for a user."""
    for prefix in (f"fh:{user_id}", f"sp:{user_id}:", f"sub:{user_id}:"):
        cache_delete_pattern(prefix)
