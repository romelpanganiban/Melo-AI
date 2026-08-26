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

from sqlalchemy.orm import Session

from database.models import User, Workspace, WorkspaceMember


TOKEN_TTL_SECONDS = 60 * 60 * 24
_SALT_BYTES = 16
_revoked_tokens: set[str] = set()


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


def verify_access_token(token: str) -> str | None:
    try:
        token_fingerprint = hashlib.sha256(token.encode()).hexdigest()
        if token_fingerprint in _revoked_tokens:
            return None
        encoded, signature = token.split(".", 1)
        expected = hmac.new(_token_secret(), encoded.encode(), hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode((signature + "===").encode())
        if not hmac.compare_digest(expected, supplied):
            return None
        payload = json.loads(base64.urlsafe_b64decode((encoded + "===").encode()))
        if payload.get("exp", 0) < time.time():
            return None
        return str(uuid.UUID(payload["sub"]))
    except (ValueError, TypeError, KeyError, binascii.Error, json.JSONDecodeError):
        return None


def revoke_access_token(token: str) -> None:
    """Revoke a token until process restart or its natural expiry."""
    _revoked_tokens.add(hashlib.sha256(token.encode()).hexdigest())


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def register_user(db: Session, email: str, password: str) -> User:
    user = User(email=email.lower(), password_hash=hash_password(password))
    db.add(user)
    db.flush()
    workspace = Workspace(name=f"{email.split('@')[0]}'s Workspace")
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
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
    membership = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner")
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership