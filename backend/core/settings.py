"""Configuration management for Melo-AI"""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """Application settings with environment variable support"""
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "false").lower() == "true"
    
    # Frontend Configuration
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # File paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "backend" / "data"
    SETTINGS_FILE: Path = DATA_DIR / "settings.json"
    CHAT_HISTORY_FILE: Path = DATA_DIR / "chat_history.json"
    SESSIONS_FILE: Path = DATA_DIR / "sessions.json"
    TRAINING_DATA_DIR: Path = DATA_DIR / "datasets"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "text")  # 'text' or 'json'
    
    # Validation
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "8000"))
    MAX_SESSION_TITLE_LENGTH: int = int(os.getenv("MAX_SESSION_TITLE_LENGTH", "255"))
    MAX_DOCUMENT_CONTENT_LENGTH: int = int(os.getenv("MAX_DOCUMENT_CONTENT_LENGTH", "2000000"))
    MAX_DATASET_BYTES: int = int(os.getenv("MAX_DATASET_BYTES", "25000000"))
    
    # Feature flags
    ENABLE_CORS: bool = os.getenv("ENABLE_CORS", "true").lower() == "true"
    ENABLE_WORKSPACE_TOOLS: bool = os.getenv("ENABLE_WORKSPACE_TOOLS", "false").lower() == "true"
    WORKSPACE_TOOLS_ROOT: str = os.getenv("WORKSPACE_TOOLS_ROOT", "").strip()
    AGENT_ALLOWED_CAPABILITIES: set[str] = {
        capability.strip().lower()
        for capability in os.getenv(
            "AGENT_ALLOWED_CAPABILITIES",
            "file:read,code:analyze,document:search",
        ).split(",")
        if capability.strip()
    }
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    RATE_LIMIT_BACKEND: str = os.getenv("RATE_LIMIT_BACKEND", "memory").strip().lower()
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    AUTH_RATE_LIMIT_REQUESTS: int = int(os.getenv("AUTH_RATE_LIMIT_REQUESTS", "10"))
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "300"))
    AUTH_COOKIE_NAME: str = os.getenv("AUTH_COOKIE_NAME", "melo_access_token")
    AUTH_CSRF_COOKIE_NAME: str = os.getenv("AUTH_CSRF_COOKIE_NAME", "melo_csrf_token")
    AUTH_CSRF_HEADER_NAME: str = os.getenv("AUTH_CSRF_HEADER_NAME", "X-CSRF-Token")
    AUTH_COOKIE_SECURE: bool = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
    ENABLE_HSTS: bool = os.getenv("ENABLE_HSTS", "false").lower() == "true"
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "").strip().lower()
    MONTHLY_TOKEN_LIMIT: int = int(os.getenv("MONTHLY_TOKEN_LIMIT", "100000"))
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin and origin.strip() and origin.strip() != "*"
    ]
    if not CORS_ORIGINS:
        CORS_ORIGINS = ["http://localhost:3000"]
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    OLLAMA_CONTEXT_SIZE: int = int(os.getenv("OLLAMA_CONTEXT_SIZE", "8192"))
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "300"))
    OLLAMA_NUM_PREDICT: int = int(os.getenv("OLLAMA_NUM_PREDICT", "512"))
    OLLAMA_KEEP_ALIVE: str = os.getenv("OLLAMA_KEEP_ALIVE", "10m")
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
    
    # Qdrant Vector Database Configuration
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY", None)
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "melo_documents")
    QDRANT_VECTOR_SIZE: int = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))  # sentence-transformers default
    QDRANT_TIMEOUT: int = int(os.getenv("QDRANT_TIMEOUT", "30"))
    QDRANT_RETRY_ATTEMPTS: int = max(1, int(os.getenv("QDRANT_RETRY_ATTEMPTS", "3")))
    QDRANT_RETRY_DELAY_SECONDS: float = max(0.0, float(os.getenv("QDRANT_RETRY_DELAY_SECONDS", "0.25")))
    QDRANT_ENABLED: bool = os.getenv("QDRANT_ENABLED", "true").lower() == "true"
    QDRANT_SCORE_THRESHOLD: float = float(os.getenv("QDRANT_SCORE_THRESHOLD", "0.25"))
    
    # Embeddings Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")  # "cpu" or "cuda"
    
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
