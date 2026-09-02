"""Tests for platform role management and admin privilege checks."""

import pytest
import uuid
from sqlalchemy.orm import Session
from core.settings import settings
from core.auth import is_platform_admin
from database.models import User
from services.auth_service import get_user_by_email, promote_user_to_admin, register_user


def test_registration_never_assigns_platform_admin(test_db):
    """Registration cannot create a platform admin from an email address."""
    admin_email = f"test-admin-{uuid.uuid4()}@example.com"
    original_admin_email = settings.ADMIN_EMAIL
    settings.ADMIN_EMAIL = admin_email
    try:
        user = register_user(test_db, admin_email, "secure_password")

        assert user.platform_role == "user"
        retrieved = get_user_by_email(test_db, admin_email)
        assert retrieved is not None
        assert retrieved.platform_role == "user"
    finally:
        settings.ADMIN_EMAIL = original_admin_email


def test_explicit_admin_bootstrap_promotes_existing_user(test_db):
    user = register_user(test_db, f"bootstrap-{uuid.uuid4()}@example.com", "secure_password")

    promoted = promote_user_to_admin(test_db, user.email)

    assert promoted is not None
    assert promoted.platform_role == "admin"
    membership = promoted.memberships[0]
    assert membership.role == "admin"


def test_regular_user_assigned_default_platform_role(test_db):
    """Verify regular users get platform_role='user' on registration."""
    user = register_user(test_db, f"user-{uuid.uuid4()}@example.com", "secure_password")
    
    assert user.platform_role == "user"
    retrieved = get_user_by_email(test_db, user.email)
    assert retrieved is not None
    assert retrieved.platform_role == "user"


def test_is_platform_admin_checks_database_role(test_db):
    """Verify is_platform_admin() checks stored platform_role, not email."""
    admin = register_user(test_db, f"admin-{uuid.uuid4()}@example.com", "password")
    admin = promote_user_to_admin(test_db, admin.email)
    assert is_platform_admin(admin) is True

    regular = register_user(test_db, f"regular-{uuid.uuid4()}@example.com", "password")
    assert is_platform_admin(regular) is False


def test_email_change_does_not_affect_admin_role(test_db):
    """Verify changing admin email does not remove admin privileges.
    
    This demonstrates that admin status is now based on stored platform_role,
    not email matching. This prevents privilege escalation/revocation from
    email changes.
    """
    admin = register_user(test_db, f"admin-{uuid.uuid4()}@example.com", "password")
    admin = promote_user_to_admin(test_db, admin.email)
    assert admin.platform_role == "admin"
    assert is_platform_admin(admin) is True

    admin.email = f"new-email-{uuid.uuid4()}@example.com"
    test_db.commit()
    test_db.refresh(admin)

    assert admin.platform_role == "admin"
    assert is_platform_admin(admin) is True


def test_admin_role_persists_across_sessions(test_db):
    """Verify admin role persists in database across session boundaries."""
    admin = register_user(test_db, f"admin-{uuid.uuid4()}@example.com", "password")
    admin = promote_user_to_admin(test_db, admin.email)
    admin_retrieved = test_db.query(User).filter(User.id == admin.id).first()
    assert admin_retrieved is not None
    assert admin_retrieved.platform_role == "admin"
    assert is_platform_admin(admin_retrieved) is True
