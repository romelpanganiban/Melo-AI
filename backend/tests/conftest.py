"""Pytest configuration and fixtures for Melo-AI tests."""

import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test_melo_ai.db"
os.environ["MELO_AUTH_SECRET"] = "test-secret-for-local-tests-please-replace"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ENABLE_WORKSPACE_TOOLS"] = "true"

import database.connection as db_connection
from database.models import Base, User, Workspace, WorkspaceMember
from database.connection import get_db
from main import app
from services.auth_service import create_access_token
from core import rate_limit


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
def test_user(test_db):
    user = User(email=f"test-{uuid.uuid4()}@example.com", password_hash="test-hash")
    test_db.add(user)
    test_db.flush()
    workspace = Workspace(name=f"Test Workspace {uuid.uuid4()}")
    test_db.add(workspace)
    test_db.flush()
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def client(test_db, test_user):
    """Create a FastAPI test client with a dependency override."""

    def override_get_db():
        yield test_db

    rate_limit._requests.clear()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(
            app,
            headers={"Authorization": f"Bearer {create_access_token(test_user.id)}"},
        )
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_session_id(test_db, test_user):
    """Create a test session in the shared file-backed database."""
    from database.repositories import SessionRepository

    repo = SessionRepository(test_db)
    workspace_id = test_user.memberships[0].workspace_id
    session = repo.create(title="Test Session", owner_id=test_user.id, workspace_id=workspace_id)
    return session.id
