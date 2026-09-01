"""Tests for document sharing authorization policy"""

import pytest
import uuid
from sqlalchemy.orm import Session

from core.authz import AuthorizationPolicy
from database.models import User, Workspace, WorkspaceMember, Document
from services.auth_service import register_user, hash_password


def test_owner_can_share_document(test_db):
    """Verify document owner can share/unshare their document."""
    # Create workspace and owner
    workspace = Workspace(name=f"Test Workspace {uuid.uuid4()}")
    test_db.add(workspace)
    test_db.flush()
    
    owner = User(email=f"owner-{uuid.uuid4()}@example.com", password_hash=hash_password("password"), platform_role="user")
    test_db.add(owner)
    test_db.flush()
    
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role="owner"))
    test_db.flush()
    
    # Create document owned by this user
    document = Document(
        workspace_id=workspace.id,
        owner_id=owner.id,
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=False
    )
    test_db.add(document)
    test_db.commit()
    
    # Owner can share
    policy = AuthorizationPolicy(test_db)
    decision = policy.authorize_document_share(owner.id, document.id, workspace.id)
    
    assert decision.allowed is True
    assert decision.status_code == 200
    assert "owner" in decision.reason


def test_non_owner_cannot_share_document(test_db):
    """Verify non-owner cannot share other's documents."""
    # Create workspace
    workspace = Workspace(name=f"Test Workspace {uuid.uuid4()}")
    test_db.add(workspace)
    test_db.flush()
    
    # Create two users
    owner = User(email=f"owner-{uuid.uuid4()}@example.com", password_hash=hash_password("password"), platform_role="user")
    test_db.add(owner)
    test_db.flush()
    
    viewer = User(email=f"viewer-{uuid.uuid4()}@example.com", password_hash=hash_password("password"), platform_role="user")
    test_db.add(viewer)
    test_db.flush()
    
    # Add both to workspace
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role="owner"))
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=viewer.id, role="viewer"))
    test_db.flush()
    
    # Create document owned by owner
    document = Document(
        workspace_id=workspace.id,
        owner_id=owner.id,
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=False
    )
    test_db.add(document)
    test_db.commit()
    
    # Viewer cannot share
    policy = AuthorizationPolicy(test_db)
    decision = policy.authorize_document_share(viewer.id, document.id, workspace.id)
    
    assert decision.allowed is False
    assert decision.status_code == 403
    assert "owner" in decision.reason


def test_shared_document_readable_by_non_owner(test_db):
    """Verify shared documents are readable by workspace members."""
    # Create workspace
    workspace = Workspace(name=f"Test Workspace {uuid.uuid4()}")
    test_db.add(workspace)
    test_db.flush()
    
    # Create two users
    owner = User(email=f"owner-{uuid.uuid4()}@example.com", password_hash=hash_password("password"), platform_role="user")
    test_db.add(owner)
    test_db.flush()
    
    reader = User(email=f"reader-{uuid.uuid4()}@example.com", password_hash=hash_password("password"), platform_role="user")
    test_db.add(reader)
    test_db.flush()
    
    # Add both to workspace
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role="owner"))
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=reader.id, role="viewer"))
    test_db.flush()
    
    # Create shared document
    document = Document(
        workspace_id=workspace.id,
        owner_id=owner.id,
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=True
    )
    test_db.add(document)
    test_db.commit()
    
    # Reader can read shared document
    policy = AuthorizationPolicy(test_db)
    decision = policy.authorize_document_read(reader.id, document.id, workspace.id)
    
    assert decision.allowed is True
    assert decision.status_code == 200
    assert "shared" in decision.reason


def test_private_document_not_readable_by_non_owner(test_db):
    """Verify private documents are not readable by non-owners."""
    # Create workspace
    workspace = Workspace(name=f"Test Workspace {uuid.uuid4()}")
    test_db.add(workspace)
    test_db.flush()
    
    # Create two users
    owner = User(email=f"owner-{uuid.uuid4()}@example.com", password_hash=hash_password("password"), platform_role="user")
    test_db.add(owner)
    test_db.flush()
    
    reader = User(email=f"reader-{uuid.uuid4()}@example.com", password_hash=hash_password("password"), platform_role="user")
    test_db.add(reader)
    test_db.flush()
    
    # Add both to workspace
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role="owner"))
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=reader.id, role="viewer"))
    test_db.flush()
    
    # Create private document
    document = Document(
        workspace_id=workspace.id,
        owner_id=owner.id,
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=False
    )
    test_db.add(document)
    test_db.commit()
    
    # Reader cannot read private document
    policy = AuthorizationPolicy(test_db)
    decision = policy.authorize_document_read(reader.id, document.id, workspace.id)
    
    assert decision.allowed is False
    assert decision.status_code == 403
    assert "not shared" in decision.reason


def test_non_owner_cannot_write_shared_document(test_db):
    """Verify non-owners cannot modify shared documents (read-only sharing)."""
    # Create workspace
    workspace = Workspace(name=f"Test Workspace {uuid.uuid4()}")
    test_db.add(workspace)
    test_db.flush()
    
    # Create two users
    owner = User(email=f"owner-{uuid.uuid4()}@example.com", password_hash=hash_password("password"), platform_role="user")
    test_db.add(owner)
    test_db.flush()
    
    editor = User(email=f"editor-{uuid.uuid4()}@example.com", password_hash=hash_password("password"), platform_role="user")
    test_db.add(editor)
    test_db.flush()
    
    # Add both to workspace
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role="owner"))
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=editor.id, role="editor"))
    test_db.flush()
    
    # Create shared document
    document = Document(
        workspace_id=workspace.id,
        owner_id=owner.id,
        filename="test.pdf",
        file_type="pdf",
        content="test content",
        is_shared=True
    )
    test_db.add(document)
    test_db.commit()
    
    # Editor can read but not write shared document
    policy = AuthorizationPolicy(test_db)
    read_decision = policy.authorize_document_read(editor.id, document.id, workspace.id)
    assert read_decision.allowed is True
    
    write_decision = policy.authorize_document_write(editor.id, document.id, workspace.id)
    assert write_decision.allowed is False
    assert write_decision.status_code == 403


def test_document_search_permission(test_db):
    """Verify users can search documents in their workspace."""
    # Create workspace and user
    workspace = Workspace(name=f"Test Workspace {uuid.uuid4()}")
    test_db.add(workspace)
    test_db.flush()
    
    user = User(email=f"user-{uuid.uuid4()}@example.com", password_hash=hash_password("password"), platform_role="user")
    test_db.add(user)
    test_db.flush()
    
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="viewer"))
    test_db.commit()
    
    # User can search documents in their workspace
    policy = AuthorizationPolicy(test_db)
    decision = policy.authorize_document_search(user.id, workspace.id)
    
    assert decision.allowed is True
    assert decision.status_code == 200


def test_document_search_denied_outside_workspace(test_db):
    """Verify users cannot search documents in other workspaces."""
    # Create two workspaces
    workspace1 = Workspace(name=f"Workspace 1 {uuid.uuid4()}")
    test_db.add(workspace1)
    test_db.flush()
    
    workspace2 = Workspace(name=f"Workspace 2 {uuid.uuid4()}")
    test_db.add(workspace2)
    test_db.flush()
    
    # Create user in workspace1 only
    user = User(email=f"user-{uuid.uuid4()}@example.com", password_hash=hash_password("password"), platform_role="user")
    test_db.add(user)
    test_db.flush()
    
    test_db.add(WorkspaceMember(workspace_id=workspace1.id, user_id=user.id, role="viewer"))
    test_db.commit()
    
    # User cannot search in workspace2
    policy = AuthorizationPolicy(test_db)
    decision = policy.authorize_document_search(user.id, workspace2.id)
    
    assert decision.allowed is False
    assert decision.status_code == 403
