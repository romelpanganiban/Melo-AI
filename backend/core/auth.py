"""FastAPI authentication dependencies."""

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User, WorkspaceMember
from services.auth_service import verify_access_token


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user_id = verify_access_token(credentials.credentials)
    user = db.query(User).filter(User.id == user_id).first() if user_id else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


def get_current_membership(
    user: User = Depends(get_current_user),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> WorkspaceMember:
    memberships = user.memberships
    membership = next((item for item in memberships if item.workspace_id == workspace_id), None) if workspace_id else (memberships[0] if memberships else None)
    if membership is None:
        detail = "Workspace membership not found" if workspace_id else "No workspace membership"
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
    return membership


def require_workspace_role(*allowed_roles: str):
    def dependency(membership: WorkspaceMember = Depends(get_current_membership)) -> WorkspaceMember:
        if membership.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient workspace role")
        return membership
    return dependency