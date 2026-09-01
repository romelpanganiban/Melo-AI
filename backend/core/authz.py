"""
Authorization policy engine for Melo-AI.

Centralized authorization decisions for workspace access, document ownership,
tool execution, and agent mutations. All authorization decisions are explicit,
testable, and auditable.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Set
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from database.models import User, WorkspaceMember, Document


class Permission(Enum):
    """Fine-grained permissions for resource access."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class WorkspaceRole(Enum):
    """Role-based workspace membership."""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    GUEST = "guest"


class ToolCapability(Enum):
    """Agent tool capabilities, role-gated."""
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_DELETE = "file:delete"
    GIT_DIFF = "git:diff"
    GIT_STAGE = "git:stage"
    GIT_COMMIT = "git:commit"
    CODE_ANALYSIS = "code:analyze"
    DOCUMENT_SEARCH = "document:search"


@dataclass
class AuthzDecision:
    """Authorization decision with explicit allow/deny and reasoning."""
    allowed: bool
    status_code: int  # 200, 403, 404, etc.
    reason: str


@dataclass
class WorkspaceContext:
    """Context for workspace-scoped operations."""
    user_id: str
    workspace_id: str
    role: WorkspaceRole
    is_admin: bool = False


class AuthorizationPolicy:
    """
    Centralized authorization policy for all Melo-AI operations.
    
    Design principles:
    - Explicit allow/deny decisions
    - All checks are database-backed (no assumptions)
    - All decisions are logged and auditable
    - Fail-closed (deny by default)
    - Role-based tool access
    """

    def __init__(self, db: Session):
        self.db = db

    def _has_document_column(self, column_name: str) -> bool:
        try:
            bind = self.db.bind
            if bind is None:
                return False
            return any(
                column["name"] == column_name
                for column in inspect(bind).get_columns("documents")
            )
        except Exception:
            return False

    def _get_document_row(self, document_id: str, workspace_id: str | None = None) -> Optional[dict]:
        if self._has_document_column("workspace_id") and self._has_document_column("is_shared"):
            doc = self.db.query(Document).filter(
                Document.id == document_id,
                Document.workspace_id == workspace_id,
            ).first()
            return doc.__dict__ if doc is not None else None

        sql = "SELECT id, owner_id, workspace_id FROM documents WHERE id = :document_id"
        params = {"document_id": document_id}
        if workspace_id is not None and self._has_document_column("workspace_id"):
            sql += " AND workspace_id = :workspace_id"
            params["workspace_id"] = workspace_id
        row = self.db.execute(text(sql), params).mappings().first()
        return dict(row) if row is not None else None

    # ============================================================================
    # Workspace Access
    # ============================================================================

    def authorize_workspace_read(self, user_id: str, workspace_id: str) -> AuthzDecision:
        """
        Check if user is a member of the workspace (can perform read operations).
        
        Args:
            user_id: UUID of authenticated user
            workspace_id: UUID of target workspace
            
        Returns:
            AuthzDecision with allow/deny and reason
        """
        try:
            membership = self.db.query(WorkspaceMember).filter(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.workspace_id == workspace_id,
            ).first()

            if membership is None:
                return AuthzDecision(
                    allowed=False,
                    status_code=403,
                    reason=f"User {user_id} is not a member of workspace {workspace_id}",
                )

            return AuthzDecision(
                allowed=True,
                status_code=200,
                reason=f"User {user_id} is member with role {membership.role}",
            )
        except Exception as e:
            return AuthzDecision(
                allowed=False,
                status_code=500,
                reason=f"Authorization check failed: {str(e)}",
            )

    def authorize_workspace_role(
        self,
        user_id: str,
        workspace_id: str,
        allowed_roles: set[str] | set[WorkspaceRole] | None = None,
    ) -> AuthzDecision:
        """Check whether the user has one of the allowed workspace roles."""
        read_decision = self.authorize_workspace_read(user_id, workspace_id)
        if not read_decision.allowed:
            return read_decision

        try:
            membership = self.db.query(WorkspaceMember).filter(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.workspace_id == workspace_id,
            ).first()

            if membership is None:
                return AuthzDecision(
                    allowed=False,
                    status_code=403,
                    reason=f"User {user_id} is not a member of workspace {workspace_id}",
                )

            normalized_role = (membership.role or "").lower()
            if allowed_roles is None:
                return AuthzDecision(
                    allowed=True,
                    status_code=200,
                    reason=f"User {user_id} has workspace role '{membership.role}'",
                )

            allowed_values = {
                role.lower() if isinstance(role, str) else role.value.lower()
                for role in allowed_roles
            }
            if normalized_role not in allowed_values:
                required = ", ".join(sorted(allowed_values))
                return AuthzDecision(
                    allowed=False,
                    status_code=403,
                    reason=f"User role '{membership.role}' is not allowed; requires one of: {required}",
                )

            return AuthzDecision(
                allowed=True,
                status_code=200,
                reason=f"User {user_id} has role '{membership.role}' and is allowed",
            )
        except Exception as e:
            return AuthzDecision(
                allowed=False,
                status_code=500,
                reason=f"Authorization check failed: {str(e)}",
            )

    def authorize_workspace_write(self, user_id: str, workspace_id: str) -> AuthzDecision:
        """
        Check if user can write to the workspace (must be owner or editor).
        
        Args:
            user_id: UUID of authenticated user
            workspace_id: UUID of target workspace
            
        Returns:
            AuthzDecision with allow/deny and reason
        """
        return self.authorize_workspace_role(user_id, workspace_id, {"owner", "admin", "editor"})

    def authorize_workspace_admin(self, user_id: str, workspace_id: str) -> AuthzDecision:
        """
        Check if user is workspace owner (admin operations).
        
        Args:
            user_id: UUID of authenticated user
            workspace_id: UUID of target workspace
            
        Returns:
            AuthzDecision with allow/deny and reason
        """
        decision = self.authorize_workspace_role(user_id, workspace_id, {"owner", "admin"})
        if not decision.allowed:
            return AuthzDecision(
                allowed=False,
                status_code=403,
                reason="Only workspace owners can perform admin operations",
            )
        return decision

    # ============================================================================
    # Document Access
    # ============================================================================

    def authorize_document_read(
        self, user_id: str, document_id: str, workspace_id: str
    ) -> AuthzDecision:
        """
        Check if user can read a document.
        
        Rules:
        - User must be member of document's workspace
        - Document must exist in that workspace
        - User must be owner OR document must be shared
        
        Args:
            user_id: UUID of authenticated user
            document_id: UUID of target document
            workspace_id: UUID of document's workspace
            
        Returns:
            AuthzDecision with allow/deny and reason
        """
        # First check workspace membership
        ws_decision = self.authorize_workspace_read(user_id, workspace_id)
        if not ws_decision.allowed:
            return ws_decision

        try:
            doc = self._get_document_row(document_id, workspace_id)

            if doc is None:
                return AuthzDecision(
                    allowed=False,
                    status_code=404,
                    reason=f"Document {document_id} not found in workspace {workspace_id}",
                )

            owner_id = doc.get("owner_id")
            is_shared = bool(doc.get("is_shared", False))

            # Owner can always read
            if owner_id == user_id:
                return AuthzDecision(
                    allowed=True,
                    status_code=200,
                    reason=f"User is document owner",
                )

            # Non-owners can read only shared documents
            if is_shared:
                return AuthzDecision(
                    allowed=True,
                    status_code=200,
                    reason=f"Document is shared with workspace",
                )

            return AuthzDecision(
                allowed=False,
                status_code=403,
                reason=f"User is not document owner and document is not shared",
            )
        except Exception as e:
            return AuthzDecision(
                allowed=False,
                status_code=500,
                reason=f"Authorization check failed: {str(e)}",
            )

    def authorize_document_write(
        self, user_id: str, document_id: str, workspace_id: str
    ) -> AuthzDecision:
        """
        Check if user can write/update a document.
        
        Rules:
        - User must be workspace member with write permission
        - User must be document owner
        
        Args:
            user_id: UUID of authenticated user
            document_id: UUID of target document
            workspace_id: UUID of document's workspace
            
        Returns:
            AuthzDecision with allow/deny and reason
        """
        # First check workspace write permission
        ws_decision = self.authorize_workspace_write(user_id, workspace_id)
        if not ws_decision.allowed:
            return ws_decision

        try:
            doc = self._get_document_row(document_id, workspace_id)

            if doc is None:
                return AuthzDecision(
                    allowed=False,
                    status_code=404,
                    reason=f"Document {document_id} not found",
                )

            # Only owner can write
            if doc.get("owner_id") != user_id:
                return AuthzDecision(
                    allowed=False,
                    status_code=403,
                    reason=f"User is not document owner",
                )

            return AuthzDecision(
                allowed=True,
                status_code=200,
                reason=f"User is document owner with workspace write permission",
            )
        except Exception as e:
            return AuthzDecision(
                allowed=False,
                status_code=500,
                reason=f"Authorization check failed: {str(e)}",
            )

    def authorize_document_delete(
        self, user_id: str, document_id: str, workspace_id: str
    ) -> AuthzDecision:
        """
        Check if user can delete a document.
        
        Rules:
        - User must be workspace owner
        - User must be document owner
        
        Args:
            user_id: UUID of authenticated user
            document_id: UUID of target document
            workspace_id: UUID of document's workspace
            
        Returns:
            AuthzDecision with allow/deny and reason
        """
        # First check workspace admin permission
        ws_decision = self.authorize_workspace_admin(user_id, workspace_id)
        if not ws_decision.allowed:
            return ws_decision

        try:
            doc = self._get_document_row(document_id, workspace_id)

            if doc is None:
                return AuthzDecision(
                    allowed=False,
                    status_code=404,
                    reason=f"Document {document_id} not found",
                )

            # Only owner can delete
            if doc.get("owner_id") != user_id:
                return AuthzDecision(
                    allowed=False,
                    status_code=403,
                    reason=f"User is not document owner",
                )

            return AuthzDecision(
                allowed=True,
                status_code=204,
                reason=f"User is document owner and workspace owner",
            )
        except Exception as e:
            return AuthzDecision(
                allowed=False,
                status_code=500,
                reason=f"Authorization check failed: {str(e)}",
            )

    def authorize_document_share(
        self, user_id: str, document_id: str, workspace_id: str
    ) -> AuthzDecision:
        """
        Check if user can share/unshare a document.
        
        Rules:
        - User must be document owner (only owner controls sharing)
        - Document must exist in workspace
        - User must have workspace write permission
        
        Args:
            user_id: UUID of authenticated user
            document_id: UUID of target document
            workspace_id: UUID of document's workspace
            
        Returns:
            AuthzDecision with allow/deny and reason
        """
        # First check workspace write permission
        ws_decision = self.authorize_workspace_write(user_id, workspace_id)
        if not ws_decision.allowed:
            return AuthzDecision(
                allowed=False,
                status_code=ws_decision.status_code,
                reason=f"{ws_decision.reason}; only the document owner can control sharing",
            )

        try:
            doc = self._get_document_row(document_id, workspace_id)

            if doc is None:
                return AuthzDecision(
                    allowed=False,
                    status_code=404,
                    reason=f"Document {document_id} not found",
                )

            # Only owner can control sharing
            if doc.get("owner_id") != user_id:
                return AuthzDecision(
                    allowed=False,
                    status_code=403,
                    reason=f"Only document owner can control sharing",
                )

            return AuthzDecision(
                allowed=True,
                status_code=200,
                reason=f"User is document owner and can control sharing",
            )
        except Exception as e:
            return AuthzDecision(
                allowed=False,
                status_code=500,
                reason=f"Authorization check failed: {str(e)}",
            )

    def authorize_document_search(
        self, user_id: str, workspace_id: str
    ) -> AuthzDecision:
        """
        Check if user can search documents in workspace.
        
        Rules:
        - User must be workspace member with read access
        - Search will return only documents user can read
          (own documents + shared documents)
        
        Args:
            user_id: UUID of authenticated user
            workspace_id: UUID of workspace
            
        Returns:
            AuthzDecision with allow/deny and reason
        """
        # Check workspace read permission
        ws_decision = self.authorize_workspace_read(user_id, workspace_id)
        if not ws_decision.allowed:
            return ws_decision

        return AuthzDecision(
            allowed=True,
            status_code=200,
            reason=f"User can search workspace documents (filtered by ownership/sharing)",
        )

    # ============================================================================
    # Agent Tool Access
    # ============================================================================

    @staticmethod
    def get_allowed_tools(role: WorkspaceRole) -> Set[ToolCapability]:
        """
        Get allowed agent tools for a given workspace role.
        
        Policy:
        - VIEWER: read-only operations
        - EDITOR: read + write operations
        - OWNER: all operations
        - GUEST: none (deny by default)
        
        Args:
            role: WorkspaceRole
            
        Returns:
            Set of allowed ToolCapability
        """
        if role in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
            return {
                ToolCapability.FILE_READ,
                ToolCapability.FILE_WRITE,
                ToolCapability.FILE_DELETE,
                ToolCapability.GIT_DIFF,
                ToolCapability.GIT_STAGE,
                ToolCapability.GIT_COMMIT,
                ToolCapability.CODE_ANALYSIS,
                ToolCapability.DOCUMENT_SEARCH,
            }
        elif role == WorkspaceRole.EDITOR:
            return {
                ToolCapability.FILE_READ,
                ToolCapability.FILE_WRITE,
                ToolCapability.GIT_DIFF,
                ToolCapability.GIT_STAGE,
                ToolCapability.CODE_ANALYSIS,
                ToolCapability.DOCUMENT_SEARCH,
            }
        elif role == WorkspaceRole.VIEWER:
            return {
                ToolCapability.FILE_READ,
                ToolCapability.CODE_ANALYSIS,
                ToolCapability.DOCUMENT_SEARCH,
            }
        else:  # GUEST or unknown
            return set()

    def authorize_tool_execution(
        self, user_id: str, workspace_id: str, tool: ToolCapability
    ) -> AuthzDecision:
        """
        Check if user can execute an agent tool in a workspace.
        
        Args:
            user_id: UUID of authenticated user
            workspace_id: UUID of target workspace
            tool: ToolCapability to execute
            
        Returns:
            AuthzDecision with allow/deny and reason
        """
        # First check workspace membership
        ws_decision = self.authorize_workspace_read(user_id, workspace_id)
        if not ws_decision.allowed:
            return ws_decision

        try:
            membership = self.db.query(WorkspaceMember).filter(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.workspace_id == workspace_id,
            ).first()

            # Parse role
            try:
                role = WorkspaceRole[membership.role.upper()]
            except KeyError:
                return AuthzDecision(
                    allowed=False,
                    status_code=403,
                    reason=f"Unknown workspace role: {membership.role}",
                )

            allowed_tools = self.get_allowed_tools(role)
            if tool not in allowed_tools:
                return AuthzDecision(
                    allowed=False,
                    status_code=403,
                    reason=f"Tool {tool.value} not allowed for role {role.value}",
                )

            return AuthzDecision(
                allowed=True,
                status_code=200,
                reason=f"User can execute tool {tool.value}",
            )
        except Exception as e:
            return AuthzDecision(
                allowed=False,
                status_code=500,
                reason=f"Authorization check failed: {str(e)}",
            )

    # ============================================================================
    # Approval Token Access
    # ============================================================================

    def authorize_approval_consumption(
        self,
        user_id: str,
        workspace_id: str,
        approval_token_user_id: str,
        approval_token_workspace_id: str,
    ) -> AuthzDecision:
        """
        Check if a user can consume an approval token.
        
        Rules:
        - Token was issued to this user
        - Token is scoped to this workspace
        - Token has not expired
        - Token has not been used
        
        Note: Actual token validation (expiry, usage) handled by ApprovalService.
        This checks the user/workspace binding.
        
        Args:
            user_id: UUID of user attempting to use token
            workspace_id: UUID of target workspace
            approval_token_user_id: UUID of user token was issued to
            approval_token_workspace_id: UUID of workspace token is scoped to
            
        Returns:
            AuthzDecision with allow/deny and reason
        """
        if user_id != approval_token_user_id:
            return AuthzDecision(
                allowed=False,
                status_code=403,
                reason=f"Approval token issued to different user",
            )

        if workspace_id != approval_token_workspace_id:
            return AuthzDecision(
                allowed=False,
                status_code=403,
                reason=f"Approval token scoped to different workspace",
            )

        return AuthzDecision(
            allowed=True,
            status_code=200,
            reason=f"Approval token binding valid",
        )
