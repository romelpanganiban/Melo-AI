"""Pytest configuration and fixtures for Melo-AI tests."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test_melo_ai.db"

import database.connection as db_connection
from database.models import Base
from database.connection import get_db
from main import app


_test_engine = None
_test_db_session_factory = None


def pytest_configure(config):
    """Set up a shared file-based SQLite database for all tests."""
    global _test_engine, _test_db_session_factory

    db_path = Path(__file__).resolve().parent / "test_melo_ai.db"
    if db_path.exists():
        db_path.unlink()

    _test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=_test_engine)
    _test_db_session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_test_engine,
    )

    db_connection.engine = _test_engine
    db_connection.SessionLocal = _test_db_session_factory


@pytest.fixture(scope="function")
def test_db():
    """Yield a database session for a single test."""
    session = _test_db_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a FastAPI test client with a dependency override."""

    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_session_id(test_db):
    """Create a test session in the shared file-backed database."""
    from database.repositories import SessionRepository

    repo = SessionRepository(test_db)
    session = repo.create(title="Test Session")
    return session.id
