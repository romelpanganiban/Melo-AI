from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from core import rate_limit
from core.rate_limit import enforce_request_rate_limit
from core.settings import settings


def test_admin_is_exempt_from_request_limit():
    admin = SimpleNamespace(email="romelpanganiban284@gmail.com")
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
    user = SimpleNamespace(email="owner@example.com")
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
