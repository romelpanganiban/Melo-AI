from types import SimpleNamespace

import pytest

from core.errors import CreditLimitError
from core.settings import settings
from database.models import UsageLedger
from services.usage_service import enforce_credit_limit, get_usage, record_usage


def test_usage_is_recorded_and_remaining_credits_calculated(test_db, test_user):
    workspace_id = test_user.memberships[0].workspace_id
    original_limit = settings.MONTHLY_TOKEN_LIMIT
    try:
        settings.MONTHLY_TOKEN_LIMIT = 1000
        record_usage(test_db, test_user.id, workspace_id, 125)
        usage = get_usage(test_db, test_user, workspace_id)
        assert usage["used_tokens"] == 125
        assert usage["remaining_tokens"] == 875
        assert test_db.query(UsageLedger).filter(
            UsageLedger.user_id == test_user.id,
            UsageLedger.workspace_id == workspace_id,
        ).count() == 1
    finally:
        settings.MONTHLY_TOKEN_LIMIT = original_limit


def test_credit_limit_rejects_exhausted_user(test_db, test_user):
    workspace_id = test_user.memberships[0].workspace_id
    original_limit = settings.MONTHLY_TOKEN_LIMIT
    try:
        settings.MONTHLY_TOKEN_LIMIT = 100
        record_usage(test_db, test_user.id, workspace_id, 100)
        with pytest.raises(CreditLimitError) as error:
            enforce_credit_limit(test_db, test_user, workspace_id)
        assert error.value.status_code == 429
        assert error.value.details["limit_tokens"] == 100
    finally:
        settings.MONTHLY_TOKEN_LIMIT = original_limit


def test_platform_admin_is_unlimited(test_db, test_user):
    workspace_id = test_user.memberships[0].workspace_id
    admin = SimpleNamespace(id="admin-id", email=settings.ADMIN_EMAIL, platform_role="admin")
    original_limit = settings.MONTHLY_TOKEN_LIMIT
    try:
        settings.MONTHLY_TOKEN_LIMIT = 1
        enforce_credit_limit(test_db, admin, workspace_id)
        assert get_usage(test_db, admin, workspace_id)["unlimited"] is True
    finally:
        settings.MONTHLY_TOKEN_LIMIT = original_limit
