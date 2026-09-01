"""FastAPI authentication and authorization dependencies."""

from dataclasses import dataclass
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User, WorkspaceMember
from services.auth_service import verify_access_token
from core.settings import settings
from core.authz import AuthorizationPolicy, WorkspaceRole


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class WorkspaceContext:
    """
    Workspace-scoped context for authorized requests.
    
    Used by route handlers to enforce workspace isolation and track
    the authenticated user, their workspace, and their role.
    
    Attributes:
        user: Authenticated User object
        workspace_id: Target workspace UUID
        role: User's role in the workspace
        membership: WorkspaceMember record
    """
    user: User
    workspace_id: str
    role: WorkspaceRole
    membership: WorkspaceMember


def is_platform_admin(user: User) -> bool:
    return user.email.strip().lower() == settings.ADMIN_EMAIL


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    token = credentials.credentials.strip() if credentials.credentials else ""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user_id = verify_access_token(token)
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


def require_workspace_access(workspace_id: str):
    """
    Dependency factory for centralized workspace authorization.
    
    This middleware enforces that:
    1. User is authenticated
    2. User is a member of the specified workspace
    3. Membership and role are validated via AuthorizationPolicy
    
    Usage:
        @router.get("/workspaces/{workspace_id}/sessions")
        async def list_sessions(
            workspace_id: str,
            workspace_ctx: WorkspaceContext = Depends(require_workspace_access(workspace_id)),
        ):
            # workspace_ctx.user is authenticated and authorized
            # workspace_ctx.workspace_id == workspace_id (validated)
            # workspace_ctx.role is user's role in the workspace
            pass
    
    Args:
        workspace_id: Target workspace UUID (from path or parameter)
        
    Returns:
        Dependency function that returns WorkspaceContext
    """
    async def _require_workspace_access(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> WorkspaceContext:
        policy = AuthorizationPolicy(db)
        decision = policy.authorize_workspace_read(current_user.id, workspace_id)
        
        if not decision.allowed:
            raise HTTPException(status_code=decision.status_code, detail=decision.reason)
        
        membership = db.query(WorkspaceMember).filter(
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.workspace_id == workspace_id,
        ).first()
        
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Workspace membership not found"
            )
        
        try:
            role = WorkspaceRole[membership.role.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unknown workspace role: {membership.role}"
            )
        
        return WorkspaceContext(
            user=current_user,
            workspace_id=workspace_id,
            role=role,
            membership=membership,
        )
    
    return _require_workspace_access


def require_workspace_access_from_header():
    """
    Dependency factory for workspace authorization using X-Workspace-ID header.
    
    This middleware enforces that:
    1. User is authenticated
    2. X-Workspace-ID header is provided
    3. User is a member of the specified workspace
    4. Membership and role are validated via AuthorizationPolicy
    
    Usage:
        @router.get("/sessions")
        async def list_sessions(
            workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
        ):
            # workspace_ctx.user is authenticated and authorized
            # workspace_ctx.workspace_id from X-Workspace-ID header (validated)
            # workspace_ctx.role is user's role in the workspace
            pass
    
    Returns:
        Dependency function that returns WorkspaceContext
    """
    async def _require_workspace_access_from_header(
        current_user: User = Depends(get_current_user),
        workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
        db: Session = Depends(get_db),
    ) -> WorkspaceContext:
        if not workspace_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-Workspace-ID header is required"
            )
        
        policy = AuthorizationPolicy(db)
        decision = policy.authorize_workspace_read(current_user.id, workspace_id)
        
        if not decision.allowed:
            raise HTTPException(status_code=decision.status_code, detail=decision.reason)
        
        membership = db.query(WorkspaceMember).filter(
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.workspace_id == workspace_id,
        ).first()
        
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Workspace membership not found"
            )
        
        try:
            role = WorkspaceRole[membership.role.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unknown workspace role: {membership.role}"
            )
        
        return WorkspaceContext(
            user=current_user,
            workspace_id=workspace_id,
            role=role,
            membership=membership,
        )
    
    return _require_workspace_access_from_header


def require_workspace_role(*allowed_roles: str):
    def dependency(membership: WorkspaceMember = Depends(get_current_membership)) -> WorkspaceMember:
        if not settings.ENABLE_WORKSPACE_TOOLS:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Workspace tools are disabled")
        if membership.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient workspace role")
        return membership
    return dependency


def require_workspace_tools(membership: WorkspaceMember = Depends(get_current_membership)) -> WorkspaceMember:
    if not settings.ENABLE_WORKSPACE_TOOLS:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Workspace tools are disabled")
    return membership


def require_workspace_role(*allowed_roles: str):
    def dependency(membership: WorkspaceMember = Depends(get_current_membership)) -> WorkspaceMember:
        if not settings.ENABLE_WORKSPACE_TOOLS:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Workspace tools are disabled")
        if membership.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient workspace role")
        return membership
    return dependency