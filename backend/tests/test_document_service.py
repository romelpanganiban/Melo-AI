"""Tests for document service and document chunk persistence."""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import database.connection as db_connection
from database.models import Base
from database.repositories import DocumentRepository, ChunkRepository
from core.errors import ValidationError
from core.settings import settings
from services import document_service as document_service_module
from services.document_service import DocumentService


@pytest.fixture()
def file_db(tmp_path):
    """Create a file-backed SQLite database for document service tests."""
    db_path = tmp_path / "documents_test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    original_engine = db_connection.engine
    original_session_local = db_connection.SessionLocal

    db_connection.engine = engine
    db_connection.SessionLocal = session_factory

    yield session_factory, engine

    db_connection.engine = original_engine
    db_connection.SessionLocal = original_session_local


def test_chunk_text_splits_content():
    service = DocumentService()

    content = "word " * 600
    chunks = service.chunk_text(content, chunk_size=200, chunk_overlap=50)

    assert len(chunks) >= 2
    assert all(chunk for chunk in chunks)


def test_chunk_text_rejects_invalid_overlap():
    service = DocumentService()

    with pytest.raises(ValidationError):
        service.chunk_text("hello world", chunk_size=10, chunk_overlap=10)


def test_upload_document_rejects_overlong_content(file_db, monkeypatch):
    session_factory, _engine = file_db
    monkeypatch.setattr(document_service_module, "get_db_session", session_factory)

    service = DocumentService()
    oversized = "x" * (settings.MAX_DOCUMENT_CONTENT_LENGTH + 1)

    with pytest.raises(ValidationError, match="size|limit"):
        service.upload_document(
            filename="oversized.txt",
            file_type="txt",
            content=oversized,
        )


def test_upload_document_stores_document_and_chunks(file_db, monkeypatch):
    session_factory, _engine = file_db
    monkeypatch.setattr(document_service_module, "get_db_session", session_factory)

    service = DocumentService()
    result = service.upload_document(
        filename="notes.txt",
        file_type="txt",
        content="This is a short offline document that should create at least one chunk.",
    )

    inspect_session = session_factory()
    try:
        document_repo = DocumentRepository(inspect_session)
        chunk_repo = ChunkRepository(inspect_session)

        stored_document = document_repo.get_by_id(result["id"])
        stored_chunks = chunk_repo.get_by_document(result["id"])

        assert stored_document is not None
        assert stored_document.filename == "notes.txt"
        assert stored_document.chunk_count == len(stored_chunks)
        assert len(stored_chunks) >= 1
        assert stored_chunks[0].content
    finally:
        inspect_session.close()


def test_delete_document_removes_chunks(file_db, monkeypatch):
    session_factory, _engine = file_db
    monkeypatch.setattr(document_service_module, "get_db_session", session_factory)

    service = DocumentService()
    created = service.upload_document(
        filename="delete-me.txt",
        file_type="txt",
        content="Delete this document and its chunks.",
    )

    service.delete_document(created["id"])

    inspect_session = session_factory()
    try:
        document_repo = DocumentRepository(inspect_session)
        chunk_repo = ChunkRepository(inspect_session)

        assert document_repo.get_by_id(created["id"]) is None
        assert chunk_repo.get_by_document(created["id"]) == []
    finally:
        inspect_session.close()


def test_get_by_session_ignores_legacy_workspace_filter_when_schema_lacks_workspace_id(file_db):
    session_factory, _engine = file_db

    with session_factory() as session:
        session.execute(text("DROP TABLE IF EXISTS documents"))
        session.execute(text("""
            CREATE TABLE documents (
                id VARCHAR(36) PRIMARY KEY,
                owner_id VARCHAR(36),
                session_id VARCHAR(36),
                collection_id VARCHAR(36),
                filename VARCHAR(255) NOT NULL,
                file_type VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                chunk_count INTEGER NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """))
        session.execute(
            text(
                "INSERT INTO documents (id, owner_id, session_id, collection_id, filename, file_type, content, chunk_count, created_at, updated_at) "
                "VALUES (:id, :owner_id, :session_id, :collection_id, :filename, :file_type, :content, :chunk_count, :created_at, :updated_at)"
            ),
            {
                "id": "doc-legacy-1",
                "owner_id": "user-1",
                "session_id": "session-legacy-1",
                "collection_id": None,
                "filename": "legacy.txt",
                "file_type": "txt",
                "content": "Legacy content",
                "chunk_count": 1,
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00",
            },
        )
        session.commit()

    with session_factory() as session:
        documents = DocumentRepository(session).get_by_session("session-legacy-1", workspace_id="workspace-legacy")

    assert len(documents) == 1
    assert documents[0].filename == "legacy.txt"
