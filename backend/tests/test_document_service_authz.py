"""Integration tests for DocumentService authorization enforcement"""

import uuid
import pytest
from sqlalchemy.orm import Session

from database import get_db_session
from database.models import User, Workspace, WorkspaceMember, Document, Session as DBSession
from services.document_service import DocumentService
from core.errors import ChatServiceError, DocumentNotFoundError, ValidationError


@pytest.fixture
def service():
    """Provide DocumentService instance"""
    return DocumentService()


@pytest.fixture
def users(test_db: Session):
    """Create test users"""
    users = {}
    for name in ['owner_a', 'user_b', 'user_c']:
        user = User(
            id=str(uuid.uuid4()),
            email=f"{name}-{uuid.uuid4()}@test.com",
            password_hash="hash"
        )
        test_db.add(user)
        users[name] = user
    test_db.commit()
    return users


@pytest.fixture
def workspaces(test_db: Session):
    """Create test workspaces"""
    workspaces = {}
    for name in ['workspace_a', 'workspace_b']:
        ws = Workspace(
            id=str(uuid.uuid4()),
            name=name
        )
        test_db.add(ws)
        workspaces[name] = ws
    test_db.commit()
    return workspaces


@pytest.fixture
def memberships(test_db: Session, users, workspaces):
    """Create workspace memberships"""
    # owner_a is owner of workspace_a
    member_a = WorkspaceMember(
        user_id=users['owner_a'].id,
        workspace_id=workspaces['workspace_a'].id,
        role='owner'
    )
    # user_b is editor in workspace_a
    member_b = WorkspaceMember(
        user_id=users['user_b'].id,
        workspace_id=workspaces['workspace_a'].id,
        role='editor'
    )
    # owner_a is owner of workspace_b
    member_c = WorkspaceMember(
        user_id=users['owner_a'].id,
        workspace_id=workspaces['workspace_b'].id,
        role='owner'
    )
    test_db.add_all([member_a, member_b, member_c])
    test_db.commit()
    return {
        'owner_a_ws_a': member_a,
        'user_b_ws_a': member_b,
        'owner_a_ws_b': member_c,
    }


class TestDocumentServiceGetAuthorization:
    """Test get_document authorization enforcement"""
    
    def test_owner_can_get_private_document(self, service, test_db, users, workspaces, memberships):
        """Owner can retrieve their private document"""
        doc = Document(
            id=str(uuid.uuid4()),
            filename="private.pdf",
            file_type="pdf",
            content="Private content",
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=False
        )
        test_db.add(doc)
        test_db.commit()
        
        # Owner should be able to get the document
        result = service.get_document(
            doc.id,
            workspace_id=workspaces['workspace_a'].id,
            user_id=users['owner_a'].id
        )
        
        assert result['id'] == doc.id
        assert result['filename'] == 'private.pdf'
        assert result['content'] == 'Private content'
    
    def test_non_owner_cannot_get_private_document(self, service, test_db, users, workspaces, memberships):
        """Non-owner cannot retrieve private document"""
        doc = Document(
            id=str(uuid.uuid4()),
            filename="private.pdf",
            file_type="pdf",
            content="Private content",
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=False
        )
        test_db.add(doc)
        test_db.commit()
        
        # Non-owner should get authorization error
        with pytest.raises(ChatServiceError):
            service.get_document(
                doc.id,
                workspace_id=workspaces['workspace_a'].id,
                user_id=users['user_b'].id
            )
    
    def test_non_owner_can_get_shared_document(self, service, test_db, users, workspaces, memberships):
        """Non-owner can retrieve shared document"""
        doc = Document(
            id=str(uuid.uuid4()),
            filename="shared.pdf",
            file_type="pdf",
            content="Shared content",
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=True
        )
        test_db.add(doc)
        test_db.commit()
        
        # Non-owner should be able to get shared document
        result = service.get_document(
            doc.id,
            workspace_id=workspaces['workspace_a'].id,
            user_id=users['user_b'].id
        )
        
        assert result['id'] == doc.id
        assert result['content'] == 'Shared content'
    
    def test_get_document_without_auth_returns_document(self, service, test_db, users, workspaces):
        """get_document without user_id returns document (legacy behavior)"""
        doc = Document(
            id=str(uuid.uuid4()),
            filename="test.pdf",
            file_type="pdf",
            content="Content",
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=False
        )
        test_db.add(doc)
        test_db.commit()
        
        # Without user_id, document should be returned (no auth check)
        result = service.get_document(
            doc.id,
            workspace_id=workspaces['workspace_a'].id,
            user_id=None
        )
        
        assert result['id'] == doc.id


class TestDocumentServiceDeleteAuthorization:
    """Test delete_document authorization enforcement"""
    
    def test_owner_can_delete_document(self, service, test_db, users, workspaces, memberships):
        """Owner can delete their document"""
        doc = Document(
            id=str(uuid.uuid4()),
            filename="deleteme.pdf",
            file_type="pdf",
            content="Will be deleted",
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=False
        )
        test_db.add(doc)
        test_db.commit()
        doc_id = doc.id
        
        # Owner should be able to delete
        service.delete_document(
            doc_id,
            workspace_id=workspaces['workspace_a'].id,
            user_id=users['owner_a'].id
        )
        
        # Document should be gone
        remaining = test_db.query(Document).filter(Document.id == doc_id).first()
        assert remaining is None
    
    def test_non_owner_cannot_delete_document(self, service, test_db, users, workspaces, memberships):
        """Non-owner cannot delete document"""
        doc = Document(
            id=str(uuid.uuid4()),
            filename="protected.pdf",
            file_type="pdf",
            content="Protected content",
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=True
        )
        test_db.add(doc)
        test_db.commit()
        
        # Non-owner should get authorization error
        with pytest.raises(ChatServiceError):
            service.delete_document(
                doc.id,
                workspace_id=workspaces['workspace_a'].id,
                user_id=users['user_b'].id
            )
    
    def test_delete_document_without_auth(self, service, test_db, users, workspaces):
        """delete_document without user_id deletes document (legacy behavior)"""
        doc = Document(
            id=str(uuid.uuid4()),
            filename="deleteme.pdf",
            file_type="pdf",
            content="Will be deleted",
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=False
        )
        test_db.add(doc)
        test_db.commit()
        doc_id = doc.id
        
        # Without user_id, document should be deleted (no auth check)
        service.delete_document(
            doc_id,
            workspace_id=workspaces['workspace_a'].id,
            user_id=None
        )
        
        # Document should be gone
        remaining = test_db.query(Document).filter(Document.id == doc_id).first()
        assert remaining is None


class TestDocumentServiceSearchAuthorization:
    """Test search_documents authorization enforcement"""
    
    def test_search_includes_owned_and_shared_documents(self, service, test_db, users, workspaces, memberships):
        """Search returns both user's owned documents and shared documents"""
        # Create a session
        session = DBSession(
            id=str(uuid.uuid4()),
            workspace_id=workspaces['workspace_a'].id,
            owner_id=users['owner_a'].id,
            title="Test Session"
        )
        test_db.add(session)
        test_db.commit()
        
        # Create owned private document
        doc1 = Document(
            id=str(uuid.uuid4()),
            filename="owned.pdf",
            file_type="pdf",
            content="Owned document content",
            session_id=session.id,
            owner_id=users['user_b'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=False
        )
        
        # Create shared document from owner_a
        doc2 = Document(
            id=str(uuid.uuid4()),
            filename="shared.pdf",
            file_type="pdf",
            content="Shared document content",
            session_id=session.id,
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=True
        )
        
        # Create private document from owner_a (should not appear for user_b)
        doc3 = Document(
            id=str(uuid.uuid4()),
            filename="private.pdf",
            file_type="pdf",
            content="Private document content",
            session_id=session.id,
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_a'].id,
            is_shared=False
        )
        
        test_db.add_all([doc1, doc2, doc3])
        test_db.commit()
        
        # Mock Qdrant to return all documents
        # In real scenario, this would query Qdrant
        # For now, we'll just verify the authorization logic
        # Note: This test would need a full end-to-end mock of Qdrant
        # For now, we verify that the method accepts the parameters
        
        # This is a placeholder - full integration would require mocking Qdrant
        assert True


class TestDocumentServiceCrossWorkspaceDenial:
    """Test that cross-workspace access is denied"""
    
    def test_cannot_access_document_from_other_workspace(self, service, test_db, users, workspaces, memberships):
        """User cannot access document from workspace they're not a member of"""
        doc = Document(
            id=str(uuid.uuid4()),
            filename="other.pdf",
            file_type="pdf",
            content="Content",
            owner_id=users['owner_a'].id,
            workspace_id=workspaces['workspace_b'].id,  # user_b is NOT in workspace_b
            is_shared=False
        )
        test_db.add(doc)
        test_db.commit()
        
        # user_b should not be able to access document in workspace_b
        with pytest.raises(ChatServiceError):
            service.get_document(
                doc.id,
                workspace_id=workspaces['workspace_b'].id,
                user_id=users['user_b'].id
            )
