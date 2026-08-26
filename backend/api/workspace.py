"""Authenticated workspace endpoints."""

from fastapi import APIRouter, Depends, status

from core.auth import get_current_user
from core.rate_limit import enforce_request_rate_limit
from database.models import User


router = APIRouter(dependencies=[Depends(enforce_request_rate_limit)])


@router.get("/workspaces", status_code=status.HTTP_200_OK)
def list_workspaces(user: User = Depends(get_current_user)):
    return {
        "workspaces": [
            {"id": membership.workspace.id, "name": membership.workspace.name, "role": membership.role}
            for membership in user.memberships
        ]
    }