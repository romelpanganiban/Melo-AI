"""Monthly token usage tracking and credit-limit enforcement."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core.auth import is_platform_admin
from core.errors import CreditLimitError
from core.settings import settings
from database.models import UsageLedger, User


def current_period_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_usage(db: Session, user: User, workspace_id: str) -> dict:
    period_start = current_period_start()
    ledger = db.query(UsageLedger).filter(
        UsageLedger.user_id == user.id,
        UsageLedger.workspace_id == workspace_id,
        UsageLedger.period_start == period_start,
    ).first()
    used = ledger.tokens_used if ledger else 0
    unlimited = is_platform_admin(user)
    return {
        "used_tokens": used,
        "limit_tokens": None if unlimited else settings.MONTHLY_TOKEN_LIMIT,
        "remaining_tokens": None if unlimited else max(settings.MONTHLY_TOKEN_LIMIT - used, 0),
        "period_start": period_start.isoformat(),
        "unlimited": unlimited,
    }


def enforce_credit_limit(db: Session, user: User, workspace_id: str) -> None:
    if is_platform_admin(user):
        return
    usage = get_usage(db, user, workspace_id)
    if usage["used_tokens"] >= settings.MONTHLY_TOKEN_LIMIT:
        raise CreditLimitError(usage["used_tokens"], settings.MONTHLY_TOKEN_LIMIT)


def record_usage(db: Session, user_id: str, workspace_id: str, tokens: int) -> None:
    if tokens <= 0 or not user_id or not workspace_id:
        return
    period_start = current_period_start()
    ledger = db.query(UsageLedger).filter(
        UsageLedger.user_id == user_id,
        UsageLedger.workspace_id == workspace_id,
        UsageLedger.period_start == period_start,
    ).first()
    if ledger is None:
        ledger = UsageLedger(
            user_id=user_id,
            workspace_id=workspace_id,
            period_start=period_start,
            tokens_used=tokens,
        )
        db.add(ledger)
    else:
        ledger.tokens_used += tokens
    db.commit()