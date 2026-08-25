"""Authentication endpoints."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.errors import ValidationError
from core.auth import get_current_user
from database.connection import get_db
from services.auth_service import create_access_token, get_user_by_email, register_user, verify_password


router = APIRouter()


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


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(request: AuthRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, request.email):
        raise ValidationError("An account with this email already exists", field="email")
    try:
        user = register_user(db, request.email, request.password)
    except IntegrityError:
        db.rollback()
        raise ValidationError("An account with this email already exists", field="email")
    return AuthResponse(access_token=create_access_token(user.id), user_id=user.id)


@router.post("/auth/login", response_model=AuthResponse)
def login(request: AuthRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, request.email)
    if user is None or not verify_password(request.password, user.password_hash):
        raise ValidationError("Invalid email or password")
    return AuthResponse(access_token=create_access_token(user.id), user_id=user.id)


@router.get("/auth/me")
def me(user=Depends(get_current_user)):
    return {"user_id": user.id, "email": user.email}