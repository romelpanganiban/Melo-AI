"""Short-lived, single-use approvals for future side-effecting actions."""

from datetime import datetime, timedelta, timezone
import secrets

from core.errors import ValidationError


class ApprovalService:
    """Keep approvals bound to an action and target until consumed or expired."""

    TTL_SECONDS = 300

    def __init__(self):
        self._approvals: dict[str, dict] = {}

    def create(self, action: str, target: str) -> dict:
        if not action.strip() or not target.strip():
            raise ValidationError("action and target are required", field="approval")
        approval_id = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.TTL_SECONDS)
        self._approvals[approval_id] = {
            "action": action,
            "target": target,
            "expires_at": expires_at,
        }
        return {"approval_id": approval_id, "action": action, "target": target, "expires_at": expires_at.isoformat()}

    def consume(self, approval_id: str, action: str, target: str) -> bool:
        approval = self._approvals.pop(approval_id, None)
        if not approval or approval["expires_at"] <= datetime.now(timezone.utc):
            return False
        return approval["action"] == action and approval["target"] == target