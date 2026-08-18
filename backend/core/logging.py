"""Structured logging for Melo-AI"""

import logging
import json
from typing import Any, Optional
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields (excluding built-in LogRecord attributes)
        reserved_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName', 
            'levelname', 'levelno', 'lineno', 'module', 'msecs', 'message', 
            'pathname', 'process', 'processName', 'relativeCreated', 'thread', 
            'threadName', 'exc_info', 'exc_text', 'stack_info', 'getMessage'
        }
        
        for key, value in record.__dict__.items():
            if key not in reserved_attrs and not key.startswith('_'):
                try:
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Text log formatter (default)"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Format the timestamp
        asctime = self.formatTime(record, self.datefmt)
        
        log_message = (
            f"{asctime} - "
            f"{record.levelname:8} - "
            f"[{record.module}:{record.lineno}] "
            f"{record.getMessage()}"
        )
        
        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"
        
        return log_message


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_type: str = "text"
) -> logging.Logger:
    """Setup logger with specified configuration
    
    Args:
        name: Logger name
        level: Logging level
        format_type: "text" or "json"
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to prevent duplicates
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Set formatter based on type
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter(
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# Create default logger
logger = setup_logger("melo-ai", level=logging.INFO, format_type="text")


def log_info(message: str, **extra: Any) -> None:
    """Log info message with extra fields"""
    logger.info(message, extra=extra)


def log_error(message: str, **extra: Any) -> None:
    """Log error message with extra fields"""
    logger.error(message, extra=extra)


def log_warning(message: str, **extra: Any) -> None:
    """Log warning message with extra fields"""
    logger.warning(message, extra=extra)


def log_debug(message: str, **extra: Any) -> None:
    """Log debug message with extra fields"""
    logger.debug(message, extra=extra)
