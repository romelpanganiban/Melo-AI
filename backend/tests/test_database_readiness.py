from unittest.mock import MagicMock

import pytest

from core.errors import ChatServiceError
from database.connection import validate_migration_state


def _engine_with_revision(revision: str | None):
    engine = MagicMock()
    inspector = MagicMock()
    inspector.get_table_names.return_value = [] if revision is None else ["alembic_version"]
    connection = MagicMock()
    connection.execute.return_value.scalar.return_value = revision
    engine.connect.return_value.__enter__.return_value = connection
    return engine, inspector


def test_readiness_rejects_missing_alembic_version(monkeypatch):
    engine, inspector = _engine_with_revision(None)
    monkeypatch.setattr("database.connection.inspect", lambda _: inspector)

    with pytest.raises(ChatServiceError, match="alembic upgrade head"):
        validate_migration_state(engine)


def test_readiness_rejects_outdated_revision(monkeypatch):
    engine, inspector = _engine_with_revision("0002_workspaces")
    monkeypatch.setattr("database.connection.inspect", lambda _: inspector)

    with pytest.raises(ChatServiceError, match="0002_workspaces"):
        validate_migration_state(engine)


def test_readiness_accepts_current_revision(monkeypatch):
    engine, inspector = _engine_with_revision("0006_phase_14a_document_sharing")
    monkeypatch.setattr("database.connection.inspect", lambda _: inspector)

    validate_migration_state(engine)