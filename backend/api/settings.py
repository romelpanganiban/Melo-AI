from fastapi import APIRouter
from pydantic import BaseModel

from services.settings_service import SettingsService

router = APIRouter()

service = SettingsService()


class SettingsRequest(BaseModel):
    model: str
    provider: str
    temperature: float


@router.get("/settings")
def get_settings():
    return manager.get_settings()


@router.put("/settings")
def update_settings(
    request: SettingsRequest
):
    return manager.update_settings(
        request.model_dump()
    )