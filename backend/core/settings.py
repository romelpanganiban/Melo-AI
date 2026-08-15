"""Configuration management for Melo-AI"""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """Application settings with environment variable support"""
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    
    # Frontend Configuration
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # File paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "backend" / "data"
    SETTINGS_FILE: Path = DATA_DIR / "settings.json"
    CHAT_HISTORY_FILE: Path = DATA_DIR / "chat_history.json"
    SESSIONS_FILE: Path = DATA_DIR / "sessions.json"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "text")  # 'text' or 'json'
    
    # Validation
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "4096"))
    MAX_SESSION_TITLE_LENGTH: int = int(os.getenv("MAX_SESSION_TITLE_LENGTH", "255"))
    
    # Feature flags
    ENABLE_CORS: bool = os.getenv("ENABLE_CORS", "true").lower() == "true"
    CORS_ORIGINS: list[str] = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    ]
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "300"))
    OLLAMA_TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    OLLAMA_TOP_P: float = float(os.getenv("OLLAMA_TOP_P", "0.9"))
    OLLAMA_TOP_K: int = int(os.getenv("OLLAMA_TOP_K", "40"))
    
    # System Prompt for AI
    SYSTEM_PROMPT: str = os.getenv(
        "SYSTEM_PROMPT",
        "You are Melo-AI, a helpful local AI assistant. "
        "You provide accurate, thoughtful responses while respecting user privacy. "
        "You run entirely on the user's local machine."
    )
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./melo_ai.db")
    DEBUG_SQL: bool = os.getenv("DEBUG_SQL", "false").lower() == "true"
    
    @classmethod
    def ensure_data_dir(cls) -> None:
        """Ensure data directory exists"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_config_dict(cls) -> dict:
        """Return configuration as dictionary"""
        return {
            "api_host": cls.API_HOST,
            "api_port": cls.API_PORT,
            "frontend_url": cls.FRONTEND_URL,
            "log_level": cls.LOG_LEVEL,
            "log_format": cls.LOG_FORMAT,
            "database_url": cls.DATABASE_URL if "password" not in cls.DATABASE_URL.lower() else "***",
        }


# Global settings instance
settings = Settings()
