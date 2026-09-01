"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.errors import ValidationError
from core.auth import get_current_user
from database.connection import get_db
from database.models import WorkspaceMember
from services.auth_service import create_access_token, ensure_default_workspace, get_user_by_email, register_user, revoke_access_token, verify_password
from core.rate_limit import enforce_auth_rate_limit


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
def register(request: AuthRequest, db: Session = Depends(get_db), _: None = Depends(enforce_auth_rate_limit)):
    if get_user_by_email(db, request.email):
        raise ValidationError("An account with this email already exists", field="email")
    try:
        user = register_user(db, request.email, request.password)
    except IntegrityError:
        db.rollback()
        raise ValidationError("An account with this email already exists", field="email")
    membership = ensure_default_workspace(db, user)
    return AuthResponse(access_token=create_access_token(user.id), user_id=user.id, workspace_id=membership.workspace_id)


@router.post("/auth/login", response_model=AuthResponse)
def login(request: AuthRequest, db: Session = Depends(get_db), _: None = Depends(enforce_auth_rate_limit)):
    user = get_user_by_email(db, request.email)
    if user is None or not verify_password(request.password, user.password_hash):
        raise ValidationError("Invalid email or password")
    membership = ensure_default_workspace(db, user)
    return AuthResponse(access_token=create_access_token(user.id), user_id=user.id, workspace_id=membership.workspace_id)


@router.get("/auth/me")
def me(user=Depends(get_current_user)):
    membership = user.memberships[0] if user.memberships else None
    return {"user_id": user.id, "email": user.email, "workspace_id": membership.workspace_id if membership else None}


@router.post("/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if credentials is None or not credentials.credentials or not credentials.credentials.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    revoke_access_token(credentials.credentials.strip(), db)
    return {"logged_out": True}