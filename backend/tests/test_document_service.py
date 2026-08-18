"""Tests for document service and document chunk persistence."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.connection as db_connection
from database.models import Base
from database.repositories import DocumentRepository, ChunkRepository
from core.errors import ValidationError
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
