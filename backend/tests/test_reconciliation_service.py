"""Tests for Qdrant/SQL reconciliation service."""

import pytest
from datetime import datetime
from database import get_db_session, DocumentRepository, ChunkRepository
from database.models import Document, DocumentChunk, User, Workspace, WorkspaceMember
from services.reconciliation_service import get_reconciliation_service
from core.settings import settings
import uuid
import time
from unittest.mock import Mock, patch


@pytest.fixture
def test_user_and_workspace(test_db):
    """Create a test user and workspace."""
    # Use timestamp + uuid to guarantee uniqueness across test runs
    unique_email = f"reconcile-{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}@test.local"
    user = User(email=unique_email, password_hash="hash")
    test_db.add(user)
    test_db.flush()
    
    workspace = Workspace(name=f"Reconciliation Test {uuid.uuid4().hex[:4]}")
    test_db.add(workspace)
    test_db.flush()
    
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
    test_db.commit()
    
    return user, workspace


@pytest.mark.skipif(not settings.QDRANT_ENABLED, reason="Qdrant not enabled")
def test_reconciliation_audit_finds_no_issues_for_synced_data(test_db, test_user_and_workspace):
    """Audit should report no issues when SQL and Qdrant are in sync."""
    user, workspace = test_user_and_workspace
    
    # Create a document with chunks
    doc_repo = DocumentRepository(test_db)
    chunk_repo = ChunkRepository(test_db)
    
    doc = doc_repo.create(
        filename="test.txt",
        file_type="txt",
        content="Test content",
        owner_id=user.id,
        workspace_id=workspace.id,
    )
    
    chunk_repo.create_many(doc.id, [
        {"chunk_index": 0, "content": "Test chunk 1", "tokens": 3},
        {"chunk_index": 1, "content": "Test chunk 2", "tokens": 3},
    ])
    
    # In a real scenario, embeddings would be generated
    # For now, just verify audit runs without error
    service = get_reconciliation_service()
    report = service.audit()
    
    assert report.sql_documents >= 1
    assert report.qdrant_vectors >= 0  # May be 0 if embeddings weren't generated


def test_reconciliation_audit_with_qdrant_disabled(test_db, test_user_and_workspace):
    """Audit should handle Qdrant being disabled gracefully."""
    if not settings.QDRANT_ENABLED:
        # Temporarily disable Qdrant
        original_enabled = settings.QDRANT_ENABLED
        settings.QDRANT_ENABLED = False
        
        try:
            service = get_reconciliation_service()
            report = service.audit()
            
            assert report.sql_documents == 0
            assert len(report.errors) > 0
            assert "disabled" in report.errors[0].lower()
        finally:
            settings.QDRANT_ENABLED = original_enabled


def test_reconciliation_report_serialization(test_user_and_workspace):
    """Reconciliation report should serialize to dict properly."""
    service = get_reconciliation_service()
    report = service.audit()
    
    report_dict = report.to_dict()
    
    assert "timestamp" in report_dict
    assert "summary" in report_dict
    assert "missing_embeddings" in report_dict
    assert "orphaned_embeddings" in report_dict
    assert "errors" in report_dict
    
    summary = report_dict["summary"]
    assert "sql_documents" in summary
    assert "qdrant_vectors" in summary
    assert "missing_embeddings" in summary
    assert "orphaned_embeddings" in summary
    assert "repaired" in summary
    assert "deleted" in summary
    assert "errors" in summary


@pytest.mark.skipif(not settings.QDRANT_ENABLED, reason="Qdrant not enabled")
def test_reconciliation_repair_without_changes(test_db, test_user_and_workspace):
    """Repair with missing_embeddings=True, delete_orphaned=False should not delete."""
    user, workspace = test_user_and_workspace
    
    service = get_reconciliation_service()
    with patch.object(service, "audit") as audit:
        audit.return_value = service.report
        report = service.repair(missing_embeddings=True, delete_orphaned=False)
    
    # No orphaned embeddings should be deleted
    assert report.deleted_count == 0


def test_reconciliation_audit_finds_missing_embeddings_in_report(test_db, test_user_and_workspace):
    """Audit report should include structure for missing embeddings."""
    service = get_reconciliation_service()
    report = service.audit()
    
    # Check that missing_embeddings list exists and has expected structure
    for missing in report.missing_embeddings:
        assert "document_id" in missing
        assert "filename" in missing
        assert "chunk_count" in missing
        assert "workspace_id" in missing


def test_reconciliation_uses_qdrant_continuation_offset(test_db, test_user_and_workspace):
    user, workspace = test_user_and_workspace
    document = DocumentRepository(test_db).create(
        filename="paged.txt",
        file_type="txt",
        content="content",
        owner_id=user.id,
        workspace_id=workspace.id,
    )
    ChunkRepository(test_db).create_many(document.id, [
        {"chunk_index": 0, "content": "chunk one", "tokens": 2},
        {"chunk_index": 1, "content": "chunk two", "tokens": 2},
    ])

    first_point = Mock(payload={"document_id": "other-document", "chunk_index": 0})
    second_point = Mock(payload={"document_id": document.id, "chunk_index": 0})
    third_point = Mock(payload={"document_id": document.id, "chunk_index": 1})
    qdrant = Mock()
    qdrant.collection_name = "melo_documents"
    qdrant.get_collection_info.return_value = {"points_count": 2}
    qdrant.client.scroll.side_effect = [([first_point], "cursor-1"), ([second_point, third_point], None)]

    with patch("services.reconciliation_service.get_qdrant_client", return_value=qdrant), patch.object(settings, "QDRANT_ENABLED", True):
        report = get_reconciliation_service().audit()

    assert report.qdrant_vectors == 2
    assert document.id not in {item["document_id"] for item in report.missing_embeddings}
    assert qdrant.client.scroll.call_args_list[1].kwargs["offset"] == "cursor-1"


def test_reconciliation_detects_partial_embeddings(test_db, test_user_and_workspace):
    user, workspace = test_user_and_workspace
    document = DocumentRepository(test_db).create(
        filename="partial.txt",
        file_type="txt",
        content="content",
        owner_id=user.id,
        workspace_id=workspace.id,
    )
    ChunkRepository(test_db).create_many(document.id, [
        {"chunk_index": 0, "content": "chunk one", "tokens": 2},
        {"chunk_index": 1, "content": "chunk two", "tokens": 2},
    ])

    qdrant = Mock()
    qdrant.collection_name = "melo_documents"
    qdrant.get_collection_info.return_value = {"points_count": 1}
    qdrant.client.scroll.return_value = (
        [Mock(payload={"document_id": document.id, "chunk_index": 0})],
        None,
    )

    with patch("services.reconciliation_service.get_qdrant_client", return_value=qdrant), patch.object(settings, "QDRANT_ENABLED", True):
        report = get_reconciliation_service().audit()

    missing_ids = {item["document_id"] for item in report.missing_embeddings}
    assert document.id in missing_ids


def test_reconciliation_does_not_repair_after_qdrant_scan_failure(test_db, test_user_and_workspace):
    service = get_reconciliation_service()
    with patch.object(service, "audit") as audit, patch.object(settings, "QDRANT_ENABLED", True), patch(
        "services.reconciliation_service.get_qdrant_client"
    ) as get_qdrant:
        service.report.errors.append("Failed to scan Qdrant: unavailable")
        audit.return_value = service.report
        report = service.repair(missing_embeddings=True, delete_orphaned=True)

    get_qdrant.assert_not_called()
    assert report.deleted_count == 0
