"""Coding assistant analysis endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from core.errors import ChatServiceError, ValidationError
from core.logging import logger
from services.code_analysis_service import get_code_analysis_service
from services.code_assistant_service import CodeAssistantService
from services.git_service import GitService

router = APIRouter()
service = get_code_analysis_service()
assistant_service = CodeAssistantService()
git_service = GitService()


class CodeAnalysisRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=500)


class FileWriteRequest(CodeAnalysisRequest):
    content: str = Field(..., max_length=1_000_000)
    confirm: bool = False


class FileDeleteRequest(CodeAnalysisRequest):
    confirm: bool = False


class CodeAssistantRequest(CodeAnalysisRequest):
    instruction: str | None = Field(default=None, max_length=4000)


class GitStageRequest(BaseModel):
    paths: list[str] = Field(..., min_length=1, max_length=100)
    confirm: bool = False


class GitCommitRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=200)
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


@router.post("/coding/review", status_code=status.HTTP_200_OK)
def review_code(request: CodeAssistantRequest):
    """Review a workspace file with the configured local model."""
    try:
        return assistant_service.review_file(request.path, request.instruction)
    except ValidationError:
        raise
    except Exception as exc:
        logger.error("Code review failed", extra={"path": request.path})
        raise ChatServiceError("Failed to review code file") from exc


@router.post("/coding/generate", status_code=status.HTTP_200_OK)
def generate_code(request: CodeAssistantRequest):
    """Generate a proposed replacement for a workspace file."""
    try:
        return assistant_service.generate_code(request.path, request.instruction or "")
    except ValidationError:
        raise
    except Exception as exc:
        logger.error("Code generation failed", extra={"path": request.path})
        raise ChatServiceError("Failed to generate code") from exc


@router.get("/git/status", status_code=status.HTTP_200_OK)
def git_status():
    """Return the current branch and changed workspace files."""
    try:
        return git_service.status()
    except Exception as exc:
        logger.error("Git status failed")
        raise ChatServiceError("Failed to read Git status") from exc


@router.get("/git/diff", status_code=status.HTTP_200_OK)
def git_diff(path: str | None = None):
    """Return the working-tree diff, optionally limited to one workspace path."""
    try:
        return git_service.diff(path)
    except ValidationError:
        raise
    except Exception as exc:
        logger.error("Git diff failed", extra={"path": path})
        raise ChatServiceError("Failed to read Git diff") from exc


@router.post("/git/stage", status_code=status.HTTP_200_OK)
def git_stage(request: GitStageRequest):
    """Stage selected workspace paths after explicit confirmation."""
    try:
        return git_service.stage(request.paths, request.confirm)
    except ValidationError:
        raise
    except Exception as exc:
        logger.error("Git stage failed")
        raise ChatServiceError("Failed to stage Git files") from exc


@router.post("/git/commit", status_code=status.HTTP_200_OK)
def git_commit(request: GitCommitRequest):
    """Create a commit after explicit confirmation."""
    try:
        return git_service.commit(request.message, request.confirm)
    except ValidationError:
        raise
    except Exception as exc:
        logger.error("Git commit failed")
        raise ChatServiceError("Failed to create Git commit") from exc
