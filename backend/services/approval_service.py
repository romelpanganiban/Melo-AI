"""Short-lived, single-use approvals for future side-effecting actions."""

from datetime import datetime, timedelta, timezone
import secrets
import threading

from core.errors import ValidationError


class ApprovalService:
    """Keep approvals bound to an action and target until consumed or expired."""

    TTL_SECONDS = 300

    def __init__(self):
        self._approvals: dict[str, dict] = {}
        self._lock = threading.Lock()

    def create(self, action: str, target: str, owner_id: str | None = None) -> dict:
        if not action.strip() or not target.strip():
            raise ValidationError("action and target are required", field="approval")
        approval_id = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.TTL_SECONDS)
        with self._lock:
            self._approvals[approval_id] = {
                "action": action,
                "target": target,
                "owner_id": owner_id,
                "expires_at": expires_at,
            }
        return {"approval_id": approval_id, "action": action, "target": target, "expires_at": expires_at.isoformat()}

    def consume(self, approval_id: str, action: str, target: str, owner_id: str | None = None) -> bool:
        with self._lock:
            approval = self._approvals.get(approval_id)
            if not approval or approval["expires_at"] <= datetime.now(timezone.utc):
                self._approvals.pop(approval_id, None)
                return False
            if approval["action"] != action or approval["target"] != target or approval["owner_id"] != owner_id:
                return False
            self._approvals.pop(approval_id, None)
            return True


_approval_service = ApprovalService()


def get_approval_service() -> ApprovalService:
    return _approval_service