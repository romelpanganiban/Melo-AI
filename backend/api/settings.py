from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from typing import Literal

from services.settings_service import SettingsService
from core.errors import SettingsError
from core.logging import logger
from core.auth import get_current_membership, require_workspace_role
from core.rate_limit import enforce_request_rate_limit

router = APIRouter(dependencies=[Depends(enforce_request_rate_limit)])

class SettingsRequest(BaseModel):
    model: str = Field(default="qwen3:8b", min_length=1, description="Model name")
    provider: str = Field(default="ollama", min_length=1, description="Model provider (e.g., ollama)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for generation (0.0-2.0)")
    context_size: Literal[4096, 8192] = Field(default=8192, description="Ollama context window size")
    learning_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    explanation_style: Literal["clear", "concise", "detailed"] = "clear"
    quiz_difficulty: Literal["easy", "medium", "hard"] = "medium"
    project_context: dict | None = Field(default=None, description="Project roadmap and active context used by the assistant")


class SettingsResponse(BaseModel):
    model: str
    provider: str
    temperature: float
    context_size: Literal[4096, 8192]
    learning_level: Literal["beginner", "intermediate", "advanced"]
    explanation_style: Literal["clear", "concise", "detailed"]
    quiz_difficulty: Literal["easy", "medium", "hard"]
    project_context: dict | None = None


@router.get("/settings", response_model=SettingsResponse, status_code=status.HTTP_200_OK)
def get_settings(membership=Depends(get_current_membership)):
    """Get current application settings
    
    Returns:
        SettingsResponse with current configuration
        
    Raises:
        SettingsError: If settings retrieval fails
    """
    try:
        logger.info("Retrieving settings")
        settings = SettingsService(membership.workspace_id).get_settings()
        return settings
        
    except Exception as e:
        logger.error(f"Error retrieving settings: {str(e)}")
        raise SettingsError(f"Failed to retrieve settings: {str(e)}")


@router.put("/settings", response_model=SettingsResponse, status_code=status.HTTP_200_OK)
def update_settings(request: SettingsRequest, membership=Depends(require_workspace_role("owner", "admin"))):
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
        
        settings = SettingsService(membership.workspace_id).update_settings(request.model_dump())
        return settings
        
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise SettingsError(f"Failed to update settings: {str(e)}")