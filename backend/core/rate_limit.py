"""Small in-memory request limiter for local abuse protection."""

from collections import defaultdict, deque
from threading import Lock
import time

from fastapi import Depends, HTTPException, Request, status

from core.auth import get_current_membership, is_platform_admin
from core.settings import settings


_requests: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def _allow(key: str, limit: int, window: int) -> bool:
    now = time.monotonic()
    with _lock:
        timestamps = _requests[key]
        while timestamps and now - timestamps[0] >= window:
            timestamps.popleft()
        if len(timestamps) >= limit:
            return False
        timestamps.append(now)
        return True


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