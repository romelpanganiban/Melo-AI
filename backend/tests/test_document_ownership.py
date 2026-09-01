"""
Comprehensive tests for Phase 14b: Document Ownership & Access Control

Tests validate:
- Document ownership enforcement (owner-only vs. is_shared policy)
- Cross-workspace document denial
- Qdrant workspace filtering
- Document service authorization integration
"""

import pytest
import uuid
from sqlalchemy.orm import Session

from core.authz import AuthorizationPolicy, WorkspaceRole
from database.models import User, Workspace, WorkspaceMember, Document
from database.repositories import DocumentRepository


@pytest.fixture
def users():
    """Create test users with unique IDs"""
    return {
        'owner_a': User(id=str(uuid.uuid4()), email=f"owner_a_{uuid.uuid4()}@example.com", password_hash="hash"),
        'user_b': User(id=str(uuid.uuid4()), email=f"user_b_{uuid.uuid4()}@example.com", password_hash="hash"),
        'user_c': User(id=str(uuid.uuid4()), email=f"user_c_{uuid.uuid4()}@example.com", password_hash="hash"),
    }


@pytest.fixture
def workspaces():
    """Create test workspaces with unique IDs"""
    return {
        'workspace_a': Workspace(id=str(uuid.uuid4()), name="Workspace A"),
        'workspace_b': Workspace(id=str(uuid.uuid4()), name="Workspace B"),
    }


@pytest.fixture
def memberships(test_db: Session, users, workspaces):
    """Create workspace memberships"""
    # Workspace A: owner_a is owner, user_b is editor, user_c is viewer
    mem_a_owner = WorkspaceMember(
        user_id=users['owner_a'].id,
        workspace_id=workspaces['workspace_a'].id,
        role='owner'
    )
    
    mem_a_editor = WorkspaceMember(
        user_id=users['user_b'].id,
        workspace_id=workspaces['workspace_a'].id,
        role='editor'
    )
    
    mem_a_viewer = WorkspaceMember(
        user_id=users['user_c'].id,
        workspace_id=workspaces['workspace_a'].id,
        role='viewer'
    )
    
    # Workspace B: owner_a is owner (different workspace)
    mem_b_owner = WorkspaceMember(
        user_id=users['owner_a'].id,
        workspace_id=workspaces['workspace_b'].id,
        role='owner'
    )
    
    # Add all to database
    test_db.add_all([
        users['owner_a'], users['user_b'], users['user_c'],
        workspaces['workspace_a'], workspaces['workspace_b'],
        mem_a_owner, mem_a_editor, mem_a_viewer, mem_b_owner
    ])
    test_db.commit()
    
    return {
        'a_owner': mem_a_owner,
        'a_editor': mem_a_editor,
        'a_viewer': mem_a_viewer,
        'b_owner': mem_b_owner,
    }


@pytest.fixture
def policy(test_db: Session):
    """Create AuthorizationPolicy instance"""
    return AuthorizationPolicy(test_db)


class TestDocumentOwnershipBasic:
    """Basic document ownership tests"""
    
    def test_document_owner_can_read_private(self, test_db: Session, users, workspaces, memberships):
        """Owner can always read their private documents"""
        # Create private document owned by owner_a
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="private.pdf",
            file_type="pdf",
            content="Private content",
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=False  # PRIVATE
        )
        test_db.add(doc)
        test_db.commit()
        
        repo = DocumentRepository(test_db)
        retrieved = repo.get_by_id(doc.id, owner_id=users['owner_a'].id, workspace_id=workspaces['workspace_a'].id)
        
        assert retrieved is not None
        assert retrieved.owner_id == users['owner_a'].id
        assert retrieved.is_shared == False
    
    def test_document_owner_can_read_shared(self, test_db: Session, users, workspaces):
        """Owner can always read their shared documents"""
        workspace = Workspace(id=str(uuid.uuid4()), name="Test")
        test_db.add(workspace)
        test_db.commit()
        
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="shared.pdf",
            file_type="pdf",
            content="Shared content",
            owner_id=users['owner_a'].id,
            workspace_id=workspace.id,
            is_shared=True  # SHARED
        )
        test_db.add(doc)
        test_db.commit()
        
        repo = DocumentRepository(test_db)
        retrieved = repo.get_by_id(doc.id, owner_id=users['owner_a'].id, workspace_id=workspace.id)
        
        assert retrieved is not None
        assert retrieved.is_shared == True
    
    def test_non_owner_cannot_read_private_document(self, test_db: Session, users, workspaces):
        """Non-owner cannot read private documents"""
        workspace = Workspace(id=str(uuid.uuid4()), name="Test")
        test_db.add(workspace)
        test_db.commit()
        
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="private.pdf",
            file_type="pdf",
            content="Private content",
            owner_id=users['owner_a'].id,
            workspace_id=workspace.id,
            is_shared=False  # PRIVATE
        )
        test_db.add(doc)
        test_db.commit()
        
        repo = DocumentRepository(test_db)
        # Query as user_b (not owner) - should fail workspace filter
        retrieved = repo.get_by_id(doc.id, owner_id=users['user_b'].id, workspace_id=workspace.id)
        
        # Repository filters by owner_id if provided, so this should return None
        # (since user_b is not the owner)
        assert retrieved is None
    
    def test_non_owner_can_read_shared_document(self, test_db: Session, users, workspaces):
        """Non-owner CAN read shared documents (authorization layer enforces is_shared)"""
        workspace = Workspace(id=str(uuid.uuid4()), name="Test")
        test_db.add(workspace)
        test_db.commit()
        
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="shared.pdf",
            file_type="pdf",
            content="Shared content",
            owner_id=users['owner_a'].id,
            workspace_id=workspace.id,
            is_shared=True  # SHARED
        )
        test_db.add(doc)
        test_db.commit()
        
        repo = DocumentRepository(test_db)
        # Query without owner_id filter - should retrieve shared documents
        retrieved = repo.get_by_id(doc.id, workspace_id=workspace.id)
        
        assert retrieved is not None
        assert retrieved.is_shared == True


class TestDocumentCrossWorkspaceDenial:
    """Cross-workspace document access denial tests"""
    
    def test_document_from_workspace_a_not_accessible_in_workspace_b(
        self, test_db: Session, users, workspaces, memberships, policy
    ):
        """Document in Workspace A cannot be accessed via Workspace B query"""
        # Create document in Workspace A
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="workspace_a_doc.pdf",
            file_type="pdf",
            content="Workspace A content",
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=False
        )
        test_db.add(doc)
        test_db.commit()
        
        # owner_a is member of both workspaces
        # When accessing from workspace_b, should not find workspace_a documents
        repo = DocumentRepository(test_db)
        retrieved = repo.get_by_id(
            doc.id,
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_b'].id  # Different workspace!
        )
        
        # Should be None because workspace_id filter prevents cross-workspace access
        assert retrieved is None
    
    def test_owner_cannot_access_shared_document_from_other_workspace(
        self, test_db: Session, users, workspaces
    ):
        """Owner cannot access even a shared document when querying from wrong workspace"""
        # Create shared document in Workspace A
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="shared_doc.pdf",
            file_type="pdf",
            content="Shared content",
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=True  # Even though shared
        )
        test_db.add(doc)
        test_db.commit()
        
        repo = DocumentRepository(test_db)
        # Query from Workspace B with same owner
        retrieved = repo.get_by_id(
            doc.id,
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_b'].id  # Wrong workspace
        )
        
        # Should still be None - workspace isolation is strict
        assert retrieved is None


class TestDocumentAuthorizationPolicyIntegration:
    """Document authorization through AuthorizationPolicy"""
    
    def test_policy_allows_owner_read(self, test_db: Session, users, workspaces, policy):
        """AuthorizationPolicy allows owner to read document"""
        workspace = Workspace(id=str(uuid.uuid4()), name="Test")
        test_db.add(workspace)
        test_db.commit()
        
        # Make owner_a a member of the workspace
        member = WorkspaceMember(
            user_id=users['owner_a'].id,
            workspace_id=workspace.id,
            role='owner'
        )
        test_db.add(member)
        test_db.commit()
        
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="test.pdf",
            file_type="pdf",
            content="Content",
            owner_id=users['owner_a'].id,
            workspace_id=workspace.id,
            is_shared=False
        )
        test_db.add(doc)
        test_db.commit()
        
        # Policy check: owner reads their own private document
        decision = policy.authorize_document_read(
            users['owner_a'].id,
            doc.id,
            workspace.id
        )
        
        assert decision.allowed == True
        assert decision.status_code == 200
    
    def test_policy_denies_non_owner_private_read(self, test_db: Session, users, workspaces, policy):
        """AuthorizationPolicy denies non-owner reading private document"""
        workspace = Workspace(id=str(uuid.uuid4()), name="Test")
        test_db.add(workspace)
        test_db.commit()
        
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="test.pdf",
            file_type="pdf",
            content="Content",
            owner_id=users['owner_a'].id,
            workspace_id=workspace.id,
            is_shared=False  # PRIVATE
        )
        test_db.add(doc)
        test_db.commit()
        
        # Policy check: non-owner reads private document
        decision = policy.authorize_document_read(
            users['user_b'].id,
            doc.id,
            workspace.id
        )
        
        assert decision.allowed == False
        assert decision.status_code in (403, 404)  # Forbidden or Not Found
    
    def test_policy_allows_non_owner_shared_read(self, test_db: Session, users, workspaces, policy):
        """AuthorizationPolicy allows non-owner reading shared document"""
        workspace = Workspace(id=str(uuid.uuid4()), name="Test")
        test_db.add(workspace)
        test_db.commit()
        
        # Make both users members of the workspace
        member_a = WorkspaceMember(
            user_id=users['owner_a'].id,
            workspace_id=workspace.id,
            role='owner'
        )
        member_b = WorkspaceMember(
            user_id=users['user_b'].id,
            workspace_id=workspace.id,
            role='editor'
        )
        test_db.add_all([member_a, member_b])
        test_db.commit()
        
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="test.pdf",
            file_type="pdf",
            content="Content",
            owner_id=users['owner_a'].id,
            workspace_id=workspace.id,
            is_shared=True  # SHARED
        )
        test_db.add(doc)
        test_db.commit()
        
        # Policy check: non-owner reads shared document
        decision = policy.authorize_document_read(
            users['user_b'].id,
            doc.id,
            workspace.id
        )
        
        assert decision.allowed == True
        assert decision.status_code == 200
    
    def test_policy_denies_non_owner_write(self, test_db: Session, users, workspaces, policy):
        """AuthorizationPolicy denies non-owner from writing"""
        workspace = Workspace(id=str(uuid.uuid4()), name="Test")
        test_db.add(workspace)
        test_db.commit()
        
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="test.pdf",
            file_type="pdf",
            content="Content",
            owner_id=users['owner_a'].id,
            workspace_id=workspace.id,
            is_shared=True  # Even if shared
        )
        test_db.add(doc)
        test_db.commit()
        
        # Policy check: non-owner cannot write even to shared document
        decision = policy.authorize_document_write(
            users['user_b'].id,
            doc.id,
            workspace.id
        )
        
        assert decision.allowed == False
        assert decision.status_code == 403
    
    def test_policy_allows_owner_delete(self, test_db: Session, users, workspaces, policy):
        """AuthorizationPolicy allows owner to delete"""
        workspace = Workspace(id=str(uuid.uuid4()), name="Test")
        test_db.add(workspace)
        test_db.commit()
        
        # Make owner_a a member of the workspace
        member = WorkspaceMember(
            user_id=users['owner_a'].id,
            workspace_id=workspace.id,
            role='owner'
        )
        test_db.add(member)
        test_db.commit()
        
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="test.pdf",
            file_type="pdf",
            content="Content",
            owner_id=users['owner_a'].id,
            workspace_id=workspace.id,
            is_shared=True
        )
        test_db.add(doc)
        test_db.commit()
        
        # Policy check: owner can delete
        decision = policy.authorize_document_delete(
            users['owner_a'].id,
            doc.id,
            workspace.id
        )
        
        assert decision.allowed == True
        assert decision.status_code == 204
    
    def test_policy_denies_non_owner_delete(self, test_db: Session, users, workspaces, policy):
        """AuthorizationPolicy denies non-owner from deleting"""
        workspace = Workspace(id=str(uuid.uuid4()), name="Test")
        test_db.add(workspace)
        test_db.commit()
        
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="test.pdf",
            file_type="pdf",
            content="Content",
            owner_id=users['owner_a'].id,
            workspace_id=workspace.id,
            is_shared=True  # Even if shared
        )
        test_db.add(doc)
        test_db.commit()
        
        # Policy check: non-owner cannot delete
        decision = policy.authorize_document_delete(
            users['user_b'].id,
            doc.id,
            workspace.id
        )
        
        assert decision.allowed == False
        assert decision.status_code == 403


class TestDocumentWriteProtection:
    """Tests for write/delete access control"""
    
    def test_editor_role_cannot_write_others_documents(
        self, test_db: Session, users, workspaces, memberships, policy
    ):
        """Editor role cannot write to documents they don't own"""
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="owned_by_owner.pdf",
            file_type="pdf",
            content="Content",
            owner_id=users['owner_a'].id,  # Owned by owner_a
            workspace_id=workspaces['workspace_a'].id,
            is_shared=True
        )
        test_db.add(doc)
        test_db.commit()
        
        # user_b is editor in workspace_a but doesn't own this document
        decision = policy.authorize_document_write(
            users['user_b'].id,
            doc.id,
            workspaces['workspace_a'].id
        )
        
        assert decision.allowed == False
        assert decision.status_code == 403
    
    def test_viewer_role_cannot_delete(self, test_db: Session, users, workspaces):
        """Viewer role cannot delete any documents"""
        workspace = Workspace(id=str(uuid.uuid4()), name="Test")
        test_db.add(workspace)
        test_db.commit()
        
        # Make user_b a viewer
        membership = WorkspaceMember(
            user_id=users['user_b'].id,
            workspace_id=workspace.id,
            role='viewer'
        )
        test_db.add(membership)
        test_db.commit()
        
        doc = Document(
            id=f"doc-{uuid.uuid4()}",
            filename="test.pdf",
            file_type="pdf",
            content="Content",
            owner_id=users['user_b'].id,  # user_b owns it
            workspace_id=workspace.id,
            is_shared=True
        )
        test_db.add(doc)
        test_db.commit()
        
        policy = AuthorizationPolicy(test_db)
        # Even though user_b owns it, viewer role cannot delete
        decision = policy.authorize_document_delete(
            users['user_b'].id,
            doc.id,
            workspace.id
        )
        
        # Viewer role has limited capabilities, should deny delete
        assert decision.allowed == False or decision.status_code == 403
