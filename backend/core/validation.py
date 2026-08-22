"""Input validation utilities for Melo-AI"""

from typing import Any
from core.errors import ValidationError
from core.settings import settings


def validate_string(
    value: Any,
    field_name: str,
    min_length: int = 1,
    max_length: int = None,
    allow_empty: bool = False
) -> str:
    """Validate string input
    
    Args:
        value: Value to validate
        field_name: Name of field (for error messages)
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        allow_empty: Whether empty strings are allowed
    
    Returns:
        Validated string
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name} must be a string",
            field=field_name
        )
    
    if not allow_empty and len(value.strip()) == 0:
        raise ValidationError(
            f"{field_name} cannot be empty",
            field=field_name
        )
    
    if len(value) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters",
            field=field_name
        )
    
    if max_length is not None and len(value) > max_length:
        raise ValidationError(
            f"{field_name} cannot exceed {max_length} characters",
            field=field_name
        )
    
    return value.strip()


def validate_uuid(value: Any, field_name: str = "id") -> str:
    """Validate UUID format
    
    Args:
        value: Value to validate
        field_name: Name of field (for error messages)
    
    Returns:
        Validated UUID string
        
    Raises:
        ValidationError: If validation fails
    """
    import uuid
    
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name} must be a string",
            field=field_name
        )
    
    try:
        uuid.UUID(value)
    except ValueError:
        raise ValidationError(
            f"{field_name} is not a valid UUID",
            field=field_name
        )
    
    return value


def validate_message(message: str, max_length: int = None) -> str:
    """Validate chat message
    
    Args:
        message: Message to validate
        max_length: Maximum message length
    
    Returns:
        Validated message
        
    Raises:
        ValidationError: If validation fails
    """
    return validate_string(
        message,
        field_name="message",
        min_length=1,
        max_length=max_length if max_length is not None else settings.MAX_MESSAGE_LENGTH,
        allow_empty=False
    )


def validate_session_title(title: str, max_length: int = 255) -> str:
    """Validate session title
    
    Args:
        title: Title to validate
        max_length: Maximum title length
    
    Returns:
        Validated title
        
    Raises:
        ValidationError: If validation fails
    """
    return validate_string(
        title,
        field_name="title",
        min_length=1,
        max_length=max_length,
        allow_empty=False
    )


def validate_dict_keys(
    data: Any,
    required_keys: list[str],
    dict_name: str = "data"
) -> dict:
    """Validate that dict has required keys
    
    Args:
        data: Dictionary to validate
        required_keys: List of required keys
        dict_name: Name of dict (for error messages)
    
    Returns:
        Validated dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError(
            f"{dict_name} must be a dictionary",
        )
    
    missing_keys = set(required_keys) - set(data.keys())
    if missing_keys:
        raise ValidationError(
            f"{dict_name} is missing required fields: {', '.join(missing_keys)}",
        )
    
    return data
