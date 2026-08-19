"""Coding assistant analysis endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from core.errors import ChatServiceError, ValidationError
from core.logging import logger
from services.code_analysis_service import get_code_analysis_service

router = APIRouter()
service = get_code_analysis_service()


class CodeAnalysisRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=500)


@router.post("/analysis/code", status_code=status.HTTP_200_OK)
def analyze_code(request: CodeAnalysisRequest):
    """Analyze a workspace source file without changing it."""
    try:
        return service.analyze_file(request.path)
    except ValidationError:
        raise
    except Exception as exc:
        logger.error("Code analysis failed", extra={"path": request.path})
        raise ChatServiceError("Failed to analyze code file") from exc
