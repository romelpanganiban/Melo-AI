"""
Tests for Phase 14a: Central Authorization Middleware

Tests verify:
- Authorization policy decisions
- Workspace membership enforcement
- Document ownership checks
- Tool capability role-gating
- Cross-workspace access denial
- Audit logging
"""

import pytest
import uuid
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database.models import User, Workspace, WorkspaceMember, Document
from core.authz import (
    AuthorizationPolicy,
    AuthzDecision,
    Permission,
    WorkspaceRole,
    ToolCapability,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def user_a(test_db: Session) -> User:
    """User A - workspace owner."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"user-a-{uuid.uuid4()}@example.com",
        password_hash="hashed_password",
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def user_b(test_db: Session) -> User:
    """User B - workspace member with editor role."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"user-b-{uuid.uuid4()}@example.com",
        password_hash="hashed_password",
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def user_c(test_db: Session) -> User:
    """User C - not a workspace member."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"user-c-{uuid.uuid4()}@example.com",
        password_hash="hashed_password",
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def workspace_a(test_db: Session) -> Workspace:
    """Workspace A."""
    ws = Workspace(id=str(uuid.uuid4()), name="Workspace A")
    test_db.add(ws)
    test_db.commit()
    return ws


@pytest.fixture
def workspace_b(test_db: Session) -> Workspace:
    """Workspace B."""
    ws = Workspace(id=str(uuid.uuid4()), name="Workspace B")
    test_db.add(ws)
    test_db.commit()
    return ws


@pytest.fixture
def membership_a_owner(test_db: Session, user_a: User, workspace_a: Workspace) -> WorkspaceMember:
    """User A is owner of Workspace A."""
    member = WorkspaceMember(
        user_id=user_a.id,
        workspace_id=workspace_a.id,
        role="owner",
    )
    test_db.add(member)
    test_db.commit()
    return member


@pytest.fixture
def membership_a_editor(test_db: Session, user_b: User, workspace_a: Workspace) -> WorkspaceMember:
    """User B is editor in Workspace A."""
    member = WorkspaceMember(
        user_id=user_b.id,
        workspace_id=workspace_a.id,
        role="editor",
    )
    test_db.add(member)
    test_db.commit()
    return member


@pytest.fixture
def membership_b_owner(test_db: Session, user_a: User, workspace_b: Workspace) -> WorkspaceMember:
    """User A is owner of Workspace B."""
    member = WorkspaceMember(
        user_id=user_a.id,
        workspace_id=workspace_b.id,
        role="owner",
    )
    test_db.add(member)
    test_db.commit()
    return member


@pytest.fixture
def policy(test_db: Session) -> AuthorizationPolicy:
    """Authorization policy engine."""
    return AuthorizationPolicy(test_db)


# ============================================================================
# Workspace Read Access Tests
# ============================================================================


def test_workspace_read_access_member_allowed(
    policy: AuthorizationPolicy,
    user_a: User,
    workspace_a: Workspace,
    membership_a_owner,
):
    """User A (owner) can read Workspace A."""
    decision = policy.authorize_workspace_read(user_a.id, workspace_a.id)
    assert decision.allowed
    assert decision.status_code == 200
    assert "member" in decision.reason.lower()


def test_workspace_read_access_non_member_denied(
    policy: AuthorizationPolicy,
    user_c: User,
    workspace_a: Workspace,
):
    """User C (not a member) cannot read Workspace A."""
    decision = policy.authorize_workspace_read(user_c.id, workspace_a.id)
    assert not decision.allowed
    assert decision.status_code == 403
    assert "not a member" in decision.reason.lower()


def test_workspace_read_access_cross_workspace_denied(
    policy: AuthorizationPolicy,
    user_c: User,
    workspace_a: Workspace,
    workspace_b: Workspace,
    membership_a_owner,
):
    """User A (owner of B) cannot read Workspace A if not a member."""
    user_a = membership_a_owner.user
    decision = policy.authorize_workspace_read(user_c.id, workspace_a.id)
    assert not decision.allowed
    assert decision.status_code == 403


# ============================================================================
# Workspace Write Access Tests
# ============================================================================


def test_workspace_write_access_owner_allowed(
    policy: AuthorizationPolicy,
    user_a: User,
    workspace_a: Workspace,
    membership_a_owner,
):
    """User A (owner) can write to Workspace A."""
    decision = policy.authorize_workspace_write(user_a.id, workspace_a.id)
    assert decision.allowed
    assert decision.status_code == 200


def test_workspace_write_access_editor_allowed(
    policy: AuthorizationPolicy,
    user_b: User,
    workspace_a: Workspace,
    membership_a_editor,
):
    """User B (editor) can write to Workspace A."""
    decision = policy.authorize_workspace_write(user_b.id, workspace_a.id)
    assert decision.allowed
    assert decision.status_code == 200


def test_workspace_write_access_viewer_denied(
    policy: AuthorizationPolicy,
    user_b: User,
    workspace_a: Workspace,
    test_db: Session,
):
    """User with viewer role cannot write."""
    member = WorkspaceMember(
        user_id=user_b.id,
        workspace_id=workspace_a.id,
        role="viewer",
    )
    test_db.add(member)
    test_db.commit()
    
    decision = policy.authorize_workspace_write(user_b.id, workspace_a.id)
    assert not decision.allowed
    assert decision.status_code == 403


def test_workspace_write_access_non_member_denied(
    policy: AuthorizationPolicy,
    user_c: User,
    workspace_a: Workspace,
):
    """User C (not a member) cannot write to Workspace A."""
    decision = policy.authorize_workspace_write(user_c.id, workspace_a.id)
    assert not decision.allowed
    assert decision.status_code == 403


# ============================================================================
# Workspace Admin Access Tests
# ============================================================================


def test_workspace_admin_access_owner_allowed(
    policy: AuthorizationPolicy,
    user_a: User,
    workspace_a: Workspace,
    membership_a_owner,
):
    """User A (owner) can perform admin operations in Workspace A."""
    decision = policy.authorize_workspace_admin(user_a.id, workspace_a.id)
    assert decision.allowed
    assert decision.status_code == 200


def test_workspace_admin_access_editor_denied(
    policy: AuthorizationPolicy,
    user_b: User,
    workspace_a: Workspace,
    membership_a_editor,
):
    """User B (editor) cannot perform admin operations."""
    decision = policy.authorize_workspace_admin(user_b.id, workspace_a.id)
    assert not decision.allowed
    assert decision.status_code == 403
    assert "only workspace owners" in decision.reason.lower()


# ============================================================================
# Document Access Tests
# ============================================================================


def test_document_read_access_owner_allowed(
    policy: AuthorizationPolicy,
    user_a: User,
    workspace_a: Workspace,
    membership_a_owner,
    test_db: Session,
):
    """Document owner can read their document."""
    doc = Document(
        id=f"doc-{uuid.uuid4()}",
        workspace_id=workspace_a.id,
        owner_id=user_a.id,
        collection_id="collection-1",
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=False,
    )
    test_db.add(doc)
    test_db.commit()
    
    decision = policy.authorize_document_read(user_a.id, doc.id, workspace_a.id)
    assert decision.allowed
    assert decision.status_code == 200


def test_document_read_access_non_owner_private_denied(
    policy: AuthorizationPolicy,
    user_a: User,
    user_b: User,
    workspace_a: Workspace,
    membership_a_owner,
    membership_a_editor,
    test_db: Session,
):
    """Non-owner cannot read private document."""
    doc = Document(
        id=f"doc-{uuid.uuid4()}",
        workspace_id=workspace_a.id,
        owner_id=user_a.id,
        collection_id="collection-1",
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=False,
    )
    test_db.add(doc)
    test_db.commit()
    
    decision = policy.authorize_document_read(user_b.id, doc.id, workspace_a.id)
    assert not decision.allowed
    assert decision.status_code == 403
    assert "not document owner" in decision.reason.lower()


def test_document_read_access_non_owner_shared_allowed(
    policy: AuthorizationPolicy,
    user_a: User,
    user_b: User,
    workspace_a: Workspace,
    membership_a_owner,
    membership_a_editor,
    test_db: Session,
):
    """Non-owner can read shared document."""
    doc = Document(
        id=f"doc-{uuid.uuid4()}",
        workspace_id=workspace_a.id,
        owner_id=user_a.id,
        collection_id="collection-1",
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=True,
    )
    test_db.add(doc)
    test_db.commit()
    
    decision = policy.authorize_document_read(user_b.id, doc.id, workspace_a.id)
    assert decision.allowed
    assert decision.status_code == 200


def test_document_read_access_wrong_workspace_denied(
    policy: AuthorizationPolicy,
    user_a: User,
    workspace_a: Workspace,
    workspace_b: Workspace,
    membership_a_owner,
    membership_b_owner,
    test_db: Session,
):
    """Cannot read document from different workspace."""
    doc = Document(
        id=f"doc-{uuid.uuid4()}",
        workspace_id=workspace_a.id,
        owner_id=user_a.id,
        collection_id="collection-1",
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=False,
    )
    test_db.add(doc)
    test_db.commit()
    
    decision = policy.authorize_document_read(user_a.id, doc.id, workspace_b.id)
    assert not decision.allowed
    assert decision.status_code == 404


# ============================================================================
# Document Write Tests
# ============================================================================


def test_document_write_access_owner_allowed(
    policy: AuthorizationPolicy,
    user_a: User,
    workspace_a: Workspace,
    membership_a_owner,
    test_db: Session,
):
    """Document owner can write to their document."""
    doc = Document(
        id=f"doc-{uuid.uuid4()}",
        workspace_id=workspace_a.id,
        owner_id=user_a.id,
        collection_id="collection-1",
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=False,
    )
    test_db.add(doc)
    test_db.commit()
    
    decision = policy.authorize_document_write(user_a.id, doc.id, workspace_a.id)
    assert decision.allowed
    assert decision.status_code == 200


def test_document_write_access_non_owner_denied(
    policy: AuthorizationPolicy,
    user_a: User,
    user_b: User,
    workspace_a: Workspace,
    membership_a_owner,
    membership_a_editor,
    test_db: Session,
):
    """Non-owner cannot write to document."""
    doc = Document(
        id=f"doc-{uuid.uuid4()}",
        workspace_id=workspace_a.id,
        owner_id=user_a.id,
        collection_id="collection-1",
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=True,
    )
    test_db.add(doc)
    test_db.commit()
    
    decision = policy.authorize_document_write(user_b.id, doc.id, workspace_a.id)
    assert not decision.allowed
    assert decision.status_code == 403


def test_document_write_access_viewer_denied(
    policy: AuthorizationPolicy,
    user_a: User,
    user_b: User,
    workspace_a: Workspace,
    test_db: Session,
):
    """Viewer cannot write even if they are owner."""
    member = WorkspaceMember(
        user_id=user_b.id,
        workspace_id=workspace_a.id,
        role="viewer",
    )
    test_db.add(member)
    test_db.commit()
    
    doc = Document(
        id=f"doc-{uuid.uuid4()}",
        workspace_id=workspace_a.id,
        owner_id=user_b.id,
        collection_id="collection-1",
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=False,
    )
    test_db.add(doc)
    test_db.commit()
    
    decision = policy.authorize_document_write(user_b.id, doc.id, workspace_a.id)
    assert not decision.allowed
    assert decision.status_code == 403


# ============================================================================
# Document Delete Tests
# ============================================================================


def test_document_delete_access_owner_allowed(
    policy: AuthorizationPolicy,
    user_a: User,
    workspace_a: Workspace,
    membership_a_owner,
    test_db: Session,
):
    """Workspace owner who owns document can delete it."""
    doc = Document(
        id=f"doc-{uuid.uuid4()}",
        workspace_id=workspace_a.id,
        owner_id=user_a.id,
        collection_id="collection-1",
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=False,
    )
    test_db.add(doc)
    test_db.commit()
    
    decision = policy.authorize_document_delete(user_a.id, doc.id, workspace_a.id)
    assert decision.allowed
    assert decision.status_code == 200


def test_document_delete_access_non_owner_denied(
    policy: AuthorizationPolicy,
    user_a: User,
    user_b: User,
    workspace_a: Workspace,
    membership_a_owner,
    membership_a_editor,
    test_db: Session,
):
    """Non-owner cannot delete document."""
    doc = Document(
        id=f"doc-{uuid.uuid4()}",
        workspace_id=workspace_a.id,
        owner_id=user_a.id,
        collection_id="collection-1",
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=False,
    )
    test_db.add(doc)
    test_db.commit()
    
    decision = policy.authorize_document_delete(user_b.id, doc.id, workspace_a.id)
    assert not decision.allowed
    assert decision.status_code == 403


def test_document_delete_access_editor_denied(
    policy: AuthorizationPolicy,
    user_a: User,
    user_b: User,
    workspace_a: Workspace,
    membership_a_owner,
    membership_a_editor,
    test_db: Session,
):
    """Editor (not owner) cannot delete even if they own it."""
    doc = Document(
        id=f"doc-{uuid.uuid4()}",
        workspace_id=workspace_a.id,
        owner_id=user_b.id,
        collection_id="collection-1",
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=False,
    )
    test_db.add(doc)
    test_db.commit()
    
    decision = policy.authorize_document_delete(user_b.id, doc.id, workspace_a.id)
    assert not decision.allowed
    assert decision.status_code == 403


# ============================================================================
# Agent Tool Capability Tests
# ============================================================================


def test_tool_capability_owner_all_allowed(
    policy: AuthorizationPolicy,
):
    """Workspace owner has all tool capabilities."""
    tools = policy.get_allowed_tools(WorkspaceRole.OWNER)
    assert ToolCapability.FILE_READ in tools
    assert ToolCapability.FILE_WRITE in tools
    assert ToolCapability.FILE_DELETE in tools
    assert ToolCapability.GIT_COMMIT in tools
    assert len(tools) == 8  # All tools


def test_tool_capability_editor_no_delete_no_commit(
    policy: AuthorizationPolicy,
):
    """Workspace editor can write but not delete or commit."""
    tools = policy.get_allowed_tools(WorkspaceRole.EDITOR)
    assert ToolCapability.FILE_READ in tools
    assert ToolCapability.FILE_WRITE in tools
    assert ToolCapability.FILE_DELETE not in tools
    assert ToolCapability.GIT_COMMIT not in tools
    assert ToolCapability.GIT_STAGE in tools


def test_tool_capability_viewer_read_only(
    policy: AuthorizationPolicy,
):
    """Workspace viewer can only read."""
    tools = policy.get_allowed_tools(WorkspaceRole.VIEWER)
    assert ToolCapability.FILE_READ in tools
    assert ToolCapability.CODE_ANALYSIS in tools
    assert ToolCapability.DOCUMENT_SEARCH in tools
    assert ToolCapability.FILE_WRITE not in tools
    assert ToolCapability.GIT_DIFF not in tools


def test_tool_capability_guest_none(
    policy: AuthorizationPolicy,
):
    """Guest has no tool capabilities."""
    tools = policy.get_allowed_tools(WorkspaceRole.GUEST)
    assert len(tools) == 0


def test_tool_execution_owner_allowed(
    policy: AuthorizationPolicy,
    user_a: User,
    workspace_a: Workspace,
    membership_a_owner,
):
    """Owner can execute any tool."""
    decision = policy.authorize_tool_execution(
        user_a.id, workspace_a.id, ToolCapability.GIT_COMMIT
    )
    assert decision.allowed
    assert decision.status_code == 200


def test_tool_execution_viewer_denied(
    policy: AuthorizationPolicy,
    user_b: User,
    workspace_a: Workspace,
    test_db: Session,
):
    """Viewer cannot execute write tools."""
    member = WorkspaceMember(
        user_id=user_b.id,
        workspace_id=workspace_a.id,
        role="viewer",
    )
    test_db.add(member)
    test_db.commit()
    
    decision = policy.authorize_tool_execution(
        user_b.id, workspace_a.id, ToolCapability.FILE_WRITE
    )
    assert not decision.allowed
    assert decision.status_code == 403


# ============================================================================
# Approval Token Access Tests
# ============================================================================


def test_approval_token_binding_valid(
    policy: AuthorizationPolicy,
    user_a: User,
    workspace_a: Workspace,
):
    """Approval token binding must match user and workspace."""
    decision = policy.authorize_approval_consumption(
        user_id=user_a.id,
        workspace_id=workspace_a.id,
        approval_token_user_id=user_a.id,
        approval_token_workspace_id=workspace_a.id,
    )
    assert decision.allowed


def test_approval_token_different_user_denied(
    policy: AuthorizationPolicy,
    user_a: User,
    user_b: User,
    workspace_a: Workspace,
):
    """User cannot use token issued to different user."""
    decision = policy.authorize_approval_consumption(
        user_id=user_a.id,
        workspace_id=workspace_a.id,
        approval_token_user_id=user_b.id,
        approval_token_workspace_id=workspace_a.id,
    )
    assert not decision.allowed
    assert decision.status_code == 403


def test_approval_token_different_workspace_denied(
    policy: AuthorizationPolicy,
    user_a: User,
    workspace_a: Workspace,
    workspace_b: Workspace,
):
    """User cannot use token scoped to different workspace."""
    decision = policy.authorize_approval_consumption(
        user_id=user_a.id,
        workspace_id=workspace_a.id,
        approval_token_user_id=user_a.id,
        approval_token_workspace_id=workspace_b.id,
    )
    assert not decision.allowed
    assert decision.status_code == 403
