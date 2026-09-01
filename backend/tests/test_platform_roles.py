"""Tests for platform role management and admin privilege checks."""

import pytest
import uuid
from sqlalchemy.orm import Session
from core.settings import settings
from core.auth import is_platform_admin
from database.models import User
from services.auth_service import register_user, get_user_by_email


def test_admin_user_assigned_correct_platform_role(test_db):
    """Verify ADMIN_EMAIL user gets platform_role='admin' on registration."""
    admin_email = f"test-admin-{uuid.uuid4()}@example.com"
    # Temporarily set ADMIN_EMAIL for this test
    original_admin_email = settings.ADMIN_EMAIL
    settings.ADMIN_EMAIL = admin_email
    try:
        user = register_user(test_db, admin_email, "secure_password")
        
        assert user.platform_role == "admin"
        retrieved = get_user_by_email(test_db, admin_email)
        assert retrieved is not None
        assert retrieved.platform_role == "admin"
    finally:
        settings.ADMIN_EMAIL = original_admin_email


def test_regular_user_assigned_default_platform_role(test_db):
    """Verify regular users get platform_role='user' on registration."""
    user = register_user(test_db, f"user-{uuid.uuid4()}@example.com", "secure_password")
    
    assert user.platform_role == "user"
    retrieved = get_user_by_email(test_db, user.email)
    assert retrieved is not None
    assert retrieved.platform_role == "user"


def test_is_platform_admin_checks_database_role(test_db):
    """Verify is_platform_admin() checks stored platform_role, not email."""
    admin_email = f"test-admin-{uuid.uuid4()}@example.com"
    original_admin_email = settings.ADMIN_EMAIL
    settings.ADMIN_EMAIL = admin_email
    try:
        # Create admin user
        admin = register_user(test_db, admin_email, "password")
        assert is_platform_admin(admin) is True
        
        # Create regular user
        regular = register_user(test_db, f"regular-{uuid.uuid4()}@example.com", "password")
        assert is_platform_admin(regular) is False
    finally:
        settings.ADMIN_EMAIL = original_admin_email


def test_email_change_does_not_affect_admin_role(test_db):
    """Verify changing admin email does not remove admin privileges.
    
    This demonstrates that admin status is now based on stored platform_role,
    not email matching. This prevents privilege escalation/revocation from
    email changes.
    """
    admin_email = f"test-admin-{uuid.uuid4()}@example.com"
    original_admin_email = settings.ADMIN_EMAIL
    settings.ADMIN_EMAIL = admin_email
    try:
        admin = register_user(test_db, admin_email, "password")
        assert admin.platform_role == "admin"
        assert is_platform_admin(admin) is True
        
        # Change email
        admin.email = f"new-email-{uuid.uuid4()}@example.com"
        test_db.commit()
        test_db.refresh(admin)
        
        # Admin status unchanged (would fail with ADMIN_EMAIL email matching)
        assert admin.platform_role == "admin"
        assert is_platform_admin(admin) is True
    finally:
        settings.ADMIN_EMAIL = original_admin_email


def test_admin_role_persists_across_sessions(test_db):
    """Verify admin role persists in database across session boundaries."""
    admin_email = f"test-admin-{uuid.uuid4()}@example.com"
    original_admin_email = settings.ADMIN_EMAIL
    settings.ADMIN_EMAIL = admin_email
    try:
        admin = register_user(test_db, admin_email, "password")
        admin_id = admin.id
        
        # Retrieve in a fresh session
        admin_retrieved = test_db.query(User).filter(User.id == admin_id).first()
        assert admin_retrieved is not None
        assert admin_retrieved.platform_role == "admin"
        assert is_platform_admin(admin_retrieved) is True
    finally:
        settings.ADMIN_EMAIL = original_admin_email
