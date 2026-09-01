"""Rate limiting with a pluggable store backend for local and distributed enforcement."""

from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
import time
from abc import ABC, abstractmethod

from fastapi import Depends, HTTPException, Request, status

try:
    import redis
except ImportError:  # pragma: no cover - optional dependency
    redis = None

from core.auth import get_current_membership, is_platform_admin
from core.settings import settings


class RateLimitStore(ABC):
    """Abstract store backend for rate-limit counters."""

    @abstractmethod
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        raise NotImplementedError


class MemoryRateLimitStore(RateLimitStore):
    """In-memory windowed limiter suitable for local development and tests."""

    def __init__(self):
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        with self._lock:
            timestamps = self._requests[key]
            while timestamps and now - timestamps[0] >= window_seconds:
                timestamps.popleft()
            if len(timestamps) >= limit:
                return False
            timestamps.append(now)
            return True


class RedisRateLimitStore(RateLimitStore):
    """Redis-backed windowed limiter for multi-instance deployments."""

    def __init__(self, redis_client):
        self._redis = redis_client

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        pipeline = self._redis.pipeline()
        now = int(time.time())
        window_key = f"ratelimit:{key}"
        script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])

        local current = redis.call('ZRANGEBYSCORE', key, 0, now)
        for _, ts in ipairs(current) do
            redis.call('ZREM', key, ts)
        end

        local count = redis.call('ZCARD', key)
        if count >= limit then
            return 0
        end

        redis.call('ZADD', key, now, now)
        redis.call('EXPIRE', key, window)
        return 1
        """
        try:
            result = self._redis.eval(script, 1, window_key, limit, window_seconds, now)
            return bool(result)
        except Exception:
            return False


_requests: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()
_default_store = MemoryRateLimitStore()


def get_rate_limit_store() -> RateLimitStore:
    """Return the active backend, defaulting to memory if Redis is unavailable."""
    backend = getattr(settings, "RATE_LIMIT_BACKEND", "memory").lower()
    if backend == "redis":
        if redis is None:
            return _default_store
        try:
            client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            client.ping()
            return RedisRateLimitStore(client)
        except Exception:
            return _default_store
    return _default_store


def _allow(key: str, limit: int, window: int) -> bool:
    return get_rate_limit_store().allow(key, limit, window)


def enforce_auth_rate_limit(request: Request) -> None:
    if settings.RATE_LIMIT_ENABLED and not _allow(
        f"auth:{request.client.host if request.client else 'unknown'}",
        settings.AUTH_RATE_LIMIT_REQUESTS,
        settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
    ):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many authentication attempts")


def enforce_request_rate_limit(
    request: Request,
    membership=Depends(get_current_membership),
) -> None:
    if not settings.RATE_LIMIT_ENABLED or is_platform_admin(membership.user):
        return
    key = f"request:{membership.workspace_id}:{membership.user_id}:{request.url.path}"
    if not _allow(key, settings.RATE_LIMIT_REQUESTS, settings.RATE_LIMIT_WINDOW_SECONDS):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")