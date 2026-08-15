from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from services.settings_service import SettingsService
from core.errors import SettingsError
from core.logging import logger

router = APIRouter()

service = SettingsService()


class SettingsRequest(BaseModel):
    model: str = Field(..., min_length=1, description="Model name")
    provider: str = Field(..., min_length=1, description="Model provider (e.g., ollama)")
    temperature: float = Field(..., ge=0.0, le=2.0, description="Temperature for generation (0.0-2.0)")


class SettingsResponse(BaseModel):
    model: str
    provider: str
    temperature: float


@router.get("/settings", response_model=SettingsResponse, status_code=status.HTTP_200_OK)
def get_settings():
    """Get current application settings
    
    Returns:
        SettingsResponse with current configuration
        
    Raises:
        SettingsError: If settings retrieval fails
    """
    try:
        logger.info("Retrieving settings")
        settings = service.get_settings()
        return settings
        
    except Exception as e:
        logger.error(f"Error retrieving settings: {str(e)}")
        raise SettingsError(f"Failed to retrieve settings: {str(e)}")


@router.put("/settings", response_model=SettingsResponse, status_code=status.HTTP_200_OK)
def update_settings(request: SettingsRequest):
    """Update application settings
    
    Args:
        request: SettingsRequest with new settings
        
    Returns:
        Updated SettingsResponse
        
    Raises:
        SettingsError: If settings update fails
    """
    try:
        logger.info(
            f"Updating settings",
            extra={
                "model": request.model,
                "provider": request.provider,
                "temperature": request.temperature
            }
        )
        
        settings = service.update_settings(request.model_dump())
        return settings
        
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise SettingsError(f"Failed to update settings: {str(e)}")