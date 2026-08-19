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


class FileWriteRequest(CodeAnalysisRequest):
    content: str = Field(..., max_length=1_000_000)
    confirm: bool = False


class FileDeleteRequest(CodeAnalysisRequest):
    confirm: bool = False


@router.delete("/files", status_code=status.HTTP_200_OK)
def delete_workspace_file(request: FileDeleteRequest):
    """Delete a workspace file only when the caller explicitly confirms."""
    try:
        return service.delete_file(request.path, request.confirm)
    except ValidationError:
        raise
    except Exception as exc:
        logger.error("File delete failed", extra={"path": request.path})
        raise ChatServiceError("Failed to delete workspace file") from exc


@router.post("/files/write", status_code=status.HTTP_200_OK)
def write_workspace_file(request: FileWriteRequest):
    """Write a workspace file only when the caller explicitly confirms."""
    try:
        return service.write_file(request.path, request.content, request.confirm)
    except ValidationError:
        raise
    except Exception as exc:
        logger.error("File write failed", extra={"path": request.path})
        raise ChatServiceError("Failed to write workspace file") from exc


@router.post("/files/read", status_code=status.HTTP_200_OK)
def read_workspace_file(request: CodeAnalysisRequest):
    """Read a UTF-8 text file inside the workspace without modifying it."""
    try:
        return service.read_file(request.path)
    except ValidationError:
        raise
    except Exception as exc:
        logger.error("File read failed", extra={"path": request.path})
        raise ChatServiceError("Failed to read workspace file") from exc


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
