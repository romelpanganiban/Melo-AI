"""Authentication endpoints."""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.errors import ValidationError
from core.auth import get_current_user
from core.settings import settings
from database.connection import get_db
from database.models import WorkspaceMember
from services.auth_service import TOKEN_TTL_SECONDS, create_access_token, ensure_default_workspace, get_user_by_email, register_user, revoke_access_token, verify_password
from core.rate_limit import enforce_auth_rate_limit
from core.logging import audit_log


router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


class AuthRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=12, max_length=256)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized.count("@") != 1 or "." not in normalized.rsplit("@", 1)[1]:
            raise ValueError("A valid email address is required")
        return normalized


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    workspace_id: str


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(request: AuthRequest, response: Response, db: Session = Depends(get_db), _: None = Depends(enforce_auth_rate_limit)):
    if get_user_by_email(db, request.email):
        raise ValidationError("An account with this email already exists", field="email")
    try:
        user = register_user(db, request.email, request.password)
    except IntegrityError:
        db.rollback()
        audit_log("auth.register", email=request.email, outcome="failure", reason="duplicate_email")
        raise ValidationError("An account with this email already exists", field="email")
    membership = ensure_default_workspace(db, user)
    token = create_access_token(user.id)
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        max_age=TOKEN_TTL_SECONDS,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="lax",
    )
    audit_log("auth.register", user_id=str(user.id), workspace_id=str(membership.workspace_id), email=request.email, outcome="success")
    return AuthResponse(access_token=token, user_id=user.id, workspace_id=membership.workspace_id)


@router.post("/auth/login", response_model=AuthResponse)
def login(request: AuthRequest, response: Response, db: Session = Depends(get_db), _: None = Depends(enforce_auth_rate_limit)):
    user = get_user_by_email(db, request.email)
    if user is None or not verify_password(request.password, user.password_hash):
        audit_log("auth.login", email=request.email, outcome="failure", reason="invalid_credentials")
        raise ValidationError("Invalid email or password")
    membership = ensure_default_workspace(db, user)
    token = create_access_token(user.id)
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        max_age=TOKEN_TTL_SECONDS,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="lax",
    )
    audit_log("auth.login", user_id=str(user.id), workspace_id=str(membership.workspace_id), email=request.email, outcome="success")
    return AuthResponse(access_token=token, user_id=user.id, workspace_id=membership.workspace_id)


@router.get("/auth/me")
def me(user=Depends(get_current_user)):
    membership = user.memberships[0] if user.memberships else None
    return {"user_id": user.id, "email": user.email, "workspace_id": membership.workspace_id if membership else None}


@router.post("/auth/logout")
def logout(
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    cookie_token: str | None = Cookie(default=None, alias=settings.AUTH_COOKIE_NAME),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token = credentials.credentials.strip() if credentials and credentials.credentials else (cookie_token or "").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    revoke_access_token(token, db)
    response.delete_cookie(key=settings.AUTH_COOKIE_NAME)
    return {"logged_out": True}