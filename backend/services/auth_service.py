"""Password hashing and signed access tokens for local authentication."""

import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core.settings import settings
from database.models import RevokedToken, User, Workspace, WorkspaceMember


TOKEN_TTL_SECONDS = 60 * 60 * 24
_SALT_BYTES = 16
_revoked_tokens: set[str] = set()


def _token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.strip().encode()).hexdigest()


def _decode_token_payload(token: str) -> dict:
    encoded, _ = token.split(".", 1)
    payload = json.loads(base64.urlsafe_b64decode((encoded + "===").encode()))
    if not isinstance(payload, dict):
        raise ValueError("token payload is invalid")
    return payload


def _token_secret() -> bytes:
    secret = os.getenv("MELO_AUTH_SECRET", "").strip()
    if len(secret) < 32 or secret.lower().startswith("replace_with_"):
        raise RuntimeError("MELO_AUTH_SECRET must be set to a random value of at least 32 characters")
    return secret.encode()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, salt_value, digest_value = encoded.split("$", 2)
        if scheme != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_value.encode())
        expected = base64.urlsafe_b64decode(digest_value.encode())
        actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(_token_secret(), encoded.encode(), hashlib.sha256).digest()
    return f"{encoded}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"


def verify_access_token(token: str, db: Session | None = None) -> str | None:
    try:
        token_fingerprint = _token_fingerprint(token)
        if token_fingerprint in _revoked_tokens:
            return None
        if db is not None:
            revoked = db.query(RevokedToken).filter(RevokedToken.token_hash == token_fingerprint).first()
            if revoked is not None:
                expires_at = revoked.expires_at
                if expires_at is None or expires_at > datetime.now(timezone.utc):
                    return None

        encoded, signature = token.split(".", 1)
        expected = hmac.new(_token_secret(), encoded.encode(), hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode((signature + "===").encode())
        if not hmac.compare_digest(expected, supplied):
            return None
        payload = _decode_token_payload(token)
        if payload.get("exp", 0) < time.time():
            return None
        return str(uuid.UUID(payload["sub"]))
    except (ValueError, TypeError, KeyError, binascii.Error, json.JSONDecodeError):
        return None


def revoke_access_token(token: str, db: Session | None = None) -> None:
    """Persistently revoke a token so it is rejected even after a fresh DB session."""
    token_fingerprint = _token_fingerprint(token)
    _revoked_tokens.add(token_fingerprint)
    if db is None:
        return

    try:
        payload = _decode_token_payload(token)
        expires_at = datetime.fromtimestamp(int(payload.get("exp", time.time() + TOKEN_TTL_SECONDS)), tz=timezone.utc)
        user_id = str(uuid.UUID(payload["sub"])) if payload.get("sub") else None
    except (ValueError, TypeError, KeyError):
        payload = {}
        expires_at = None
        user_id = None

    revoked = db.query(RevokedToken).filter(RevokedToken.token_hash == token_fingerprint).first()
    if revoked is None:
        db.add(RevokedToken(token_hash=token_fingerprint, user_id=user_id, expires_at=expires_at))
    else:
        revoked.user_id = user_id
        revoked.expires_at = expires_at
    db.commit()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def register_user(db: Session, email: str, password: str) -> User:
    platform_role = "admin" if email.lower() == settings.ADMIN_EMAIL else "user"
    user = User(email=email.lower(), password_hash=hash_password(password), platform_role=platform_role)
    db.add(user)
    db.flush()
    workspace = Workspace(name=f"{email.split('@')[0]}'s Workspace")
    db.add(workspace)
    db.flush()
    workspace_role = "admin" if platform_role == "admin" else "owner"
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=workspace_role))
    db.commit()
    db.refresh(user)
    return user


def ensure_default_workspace(db: Session, user: User) -> WorkspaceMember:
    membership = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).first()
    if membership:
        return membership
    workspace = Workspace(name=f"{user.email.split('@')[0]}'s Workspace")
    db.add(workspace)
    db.flush()
    workspace_role = "admin" if user.platform_role == "admin" else "owner"
    membership = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=workspace_role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership