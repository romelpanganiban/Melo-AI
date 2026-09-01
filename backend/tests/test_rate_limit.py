from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from core import rate_limit
from core.rate_limit import MemoryRateLimitStore, RedisRateLimitStore, enforce_request_rate_limit, get_rate_limit_store
from core.settings import settings


def test_admin_is_exempt_from_request_limit():
    admin = SimpleNamespace(email=settings.ADMIN_EMAIL, platform_role="admin")
    membership = SimpleNamespace(role="admin", workspace_id="workspace-1", user_id="user-1", user=admin)
    request = SimpleNamespace(url=SimpleNamespace(path="/chat"))

    original_enabled = settings.RATE_LIMIT_ENABLED
    original_limit = settings.RATE_LIMIT_REQUESTS
    try:
        settings.RATE_LIMIT_ENABLED = True
        settings.RATE_LIMIT_REQUESTS = 1
        enforce_request_rate_limit(request, membership)
        enforce_request_rate_limit(request, membership)
    finally:
        settings.RATE_LIMIT_ENABLED = original_enabled
        settings.RATE_LIMIT_REQUESTS = original_limit


def test_registered_owner_is_limited_with_429():
    user = SimpleNamespace(email="owner@example.com", platform_role="user")
    membership = SimpleNamespace(role="owner", workspace_id="workspace-limit", user_id="user-limit", user=user)
    request = SimpleNamespace(url=SimpleNamespace(path="/chat"))
    key = "request:workspace-limit:user-limit:/chat"
    rate_limit._requests.pop(key, None)

    original_enabled = settings.RATE_LIMIT_ENABLED
    original_limit = settings.RATE_LIMIT_REQUESTS
    original_window = settings.RATE_LIMIT_WINDOW_SECONDS
    try:
        settings.RATE_LIMIT_ENABLED = True
        settings.RATE_LIMIT_REQUESTS = 1
        settings.RATE_LIMIT_WINDOW_SECONDS = 60
        enforce_request_rate_limit(request, membership)
        with pytest.raises(HTTPException, match="Rate limit exceeded") as error:
            enforce_request_rate_limit(request, membership)
        assert error.value.status_code == 429
    finally:
        settings.RATE_LIMIT_ENABLED = original_enabled
        settings.RATE_LIMIT_REQUESTS = original_limit
        settings.RATE_LIMIT_WINDOW_SECONDS = original_window
        rate_limit._requests.pop(key, None)


def test_memory_rate_limit_store_enforces_windowed_limit():
    store = MemoryRateLimitStore()
    key = "workspace:limit:user:limit:/chat"

    assert store.allow(key, 1, 60) is True
    assert store.allow(key, 1, 60) is False


def test_get_rate_limit_store_uses_redis_when_configured(monkeypatch):
    class FakeRedisClient:
        @staticmethod
        def from_url(*args, **kwargs):
            return FakeRedisClient()

        def ping(self):
            return True

        def eval(self, *args, **kwargs):
            return 1

        def pipeline(self):
            return self

    monkeypatch.setattr(settings, "RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(
        rate_limit,
        "redis",
        SimpleNamespace(Redis=SimpleNamespace(from_url=FakeRedisClient.from_url)),
    )

    store = get_rate_limit_store()
    assert isinstance(store, RedisRateLimitStore)


def test_get_rate_limit_store_falls_back_to_memory():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(settings, "RATE_LIMIT_BACKEND", "memory")
    try:
        store = get_rate_limit_store()
        assert isinstance(store, MemoryRateLimitStore)
    finally:
        monkeypatch.undo()
