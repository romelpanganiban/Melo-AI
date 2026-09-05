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

    def create(self, action: str, target: str, owner_id: str | None = None, workspace_id: str | None = None) -> dict:
        if not action.strip() or not target.strip():
            raise ValidationError("action and target are required", field="approval")
        approval_id = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.TTL_SECONDS)
        with self._lock:
            self._approvals[approval_id] = {
                "action": action,
                "target": target,
                "owner_id": owner_id,
                "workspace_id": workspace_id,
                "expires_at": expires_at,
            }
        return {"approval_id": approval_id, "action": action, "target": target, "expires_at": expires_at.isoformat()}

    def consume(self, approval_id: str, action: str, target: str, owner_id: str | None = None, workspace_id: str | None = None) -> bool:
        with self._lock:
            approval = self._approvals.get(approval_id)
            if not approval or approval["expires_at"] <= datetime.now(timezone.utc):
                self._approvals.pop(approval_id, None)
                return False
            if approval["action"] != action or approval["target"] != target or approval["owner_id"] != owner_id or approval["workspace_id"] != workspace_id:
                return False
            self._approvals.pop(approval_id, None)
            return True

    def consume_for_request(
        self,
        approval_id: str,
        action: str,
        target: str,
        owner_id: str,
        workspace_id: str,
        policy,
    ) -> bool:
        """Validate authorization binding and consume a matching approval once."""
        approval = self._get_active_approval(approval_id)
        if approval is None:
            return False

        decision = policy.authorize_approval_consumption(
            user_id=owner_id,
            workspace_id=workspace_id,
            approval_token_user_id=approval["owner_id"],
            approval_token_workspace_id=approval["workspace_id"],
        )
        if not decision.allowed:
            return False

        return self.consume(
            approval_id,
            action,
            target,
            owner_id=owner_id,
            workspace_id=workspace_id,
        )

    def _get_active_approval(self, approval_id: str) -> dict | None:
        with self._lock:
            approval = self._approvals.get(approval_id)
            if not approval or approval["expires_at"] <= datetime.now(timezone.utc):
                self._approvals.pop(approval_id, None)
                return None
            return dict(approval)


_approval_service = ApprovalService()


def get_approval_service() -> ApprovalService:
    return _approval_service