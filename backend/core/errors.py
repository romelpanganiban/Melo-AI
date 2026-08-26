"""Comprehensive error handling for Melo-AI"""

from typing import Any, Optional
from fastapi import status


class MeloAIException(Exception):
    """Base exception for all Melo-AI errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to API response format"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class SessionNotFoundError(MeloAIException):
    """Raised when a session cannot be found"""
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="SESSION_NOT_FOUND",
            details={"session_id": session_id}
        )


class DocumentNotFoundError(MeloAIException):
    """Raised when a document is missing or inaccessible."""

    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document '{document_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DOCUMENT_NOT_FOUND",
            details={"document_id": document_id},
        )


class SettingsError(MeloAIException):
    """Raised when settings operation fails"""
    
    def __init__(self, message: str = "Settings operation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="SETTINGS_ERROR"
        )


class ValidationError(MeloAIException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


class ChatServiceError(MeloAIException):
    """Raised when chat service operation fails"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CHAT_SERVICE_ERROR"
        )


class CreditLimitError(MeloAIException):
    """Raised when a workspace has exhausted its monthly token budget."""

    def __init__(self, used: int, limit: int):
        super().__init__(
            message="Monthly token limit reached",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="CREDIT_LIMIT_EXCEEDED",
            details={"used_tokens": used, "limit_tokens": limit},
        )


class FileOperationError(MeloAIException):
    """Raised when file operation fails"""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="FILE_OPERATION_ERROR",
            details={"file_path": file_path} if file_path else {}
        )
