"""Tests for structured audit logging."""

import logging

import pytest
from fastapi import HTTPException

from core.auth import require_admin
from core.logging import audit_log


def test_audit_log_emits_structured_event(caplog):
    with caplog.at_level(logging.INFO, logger="melo-ai.audit"):
        audit_log(
            "auth.login",
            user_id="user-123",
            workspace_id="workspace-456",
            outcome="success",
            email="demo@example.com",
        )

    assert any("auth.login" in record.getMessage() for record in caplog.records)
    assert any(record.name == "melo-ai.audit" for record in caplog.records)
    assert any(getattr(record, "event", None) == "auth.login" for record in caplog.records)
    assert any(getattr(record, "user_id", None) == "user-123" for record in caplog.records)
    assert any(getattr(record, "workspace_id", None) == "workspace-456" for record in caplog.records)


def test_require_admin_logs_denial(test_db, test_user, caplog):
    with caplog.at_level(logging.INFO, logger="melo-ai.audit"):
        with pytest.raises(HTTPException, match="Admin access required"):
            require_admin(test_user.id, test_db)

    assert any(getattr(record, "event", None) == "authz.denied" for record in caplog.records)
    assert any(getattr(record, "user_id", None) == str(test_user.id) for record in caplog.records)
    assert any(getattr(record, "action", None) == "admin_access" for record in caplog.records)


def test_audit_log_redacts_sensitive_fields(caplog):
    with caplog.at_level(logging.INFO, logger="melo-ai.audit"):
        audit_log(
            "auth.token_refresh",
            user_id="user-123",
            access_token="Bearer super-secret-token",
            refresh_token="refresh-secret-value",
            outcome="success",
        )

    log_record = next(record for record in caplog.records if getattr(record, "event", None) == "auth.token_refresh")
    assert getattr(log_record, "access_token", None) == "[REDACTED]"
    assert getattr(log_record, "refresh_token", None) == "[REDACTED]"


def test_audit_log_redacts_api_keys_and_nested_secrets(caplog):
    with caplog.at_level(logging.INFO, logger="melo-ai.audit"):
        audit_log(
            "security.config_check",
            qdrant_api_key="qdrant-secret",
            details={"database_url": "postgres-secret", "safe": "visible"},
        )

    log_record = next(record for record in caplog.records if getattr(record, "event", None) == "security.config_check")
    assert getattr(log_record, "qdrant_api_key", None) == "[REDACTED]"
    assert log_record.details == {"database_url": "[REDACTED]", "safe": "visible"}
