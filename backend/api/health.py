from fastapi import APIRouter, status
from pathlib import Path

from core.settings import settings
from core.logging import logger
from services.ollama_client import OllamaClient
from services.qdrant_client import get_qdrant_client

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
def health():
    """Health check endpoint
    
    Returns:
        Health status with component checks
    """
    try:
        # Check data directory
        data_dir_ok = settings.DATA_DIR.exists()
        
        # Check files
        settings_file_ok = settings.SETTINGS_FILE.exists()
        sessions_file_ok = settings.SESSIONS_FILE.exists()
        history_file_ok = settings.CHAT_HISTORY_FILE.exists()
        
        all_ok = data_dir_ok and settings_file_ok

        ollama_client = OllamaClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=min(settings.OLLAMA_TIMEOUT, 10),
        )
        ollama_ok = ollama_client.is_available()
        ollama_model_ok = ollama_ok and ollama_client.is_model_available()

        qdrant_ok = False
        if settings.QDRANT_ENABLED:
            try:
                qdrant_ok = get_qdrant_client().is_available()
            except Exception as e:
                logger.warning(f"Qdrant health check failed: {str(e)}")
        
        logger.info(
            "Health check performed",
            extra={
                "data_dir_ok": data_dir_ok,
                "settings_file_ok": settings_file_ok,
                "sessions_file_ok": sessions_file_ok,
                "history_file_ok": history_file_ok
            }
        )
        
        return {
            "status": "healthy" if all_ok and ollama_ok and ollama_model_ok else "degraded",
            "service": "Melo-AI",
            "version": "0.1.0",
            "components": {
                "data_directory": "ok" if data_dir_ok else "missing",
                "settings_file": "ok" if settings_file_ok else "missing",
                "sessions_file": "ok" if sessions_file_ok else "missing",
                "chat_history_file": "ok" if history_file_ok else "missing",
                "ollama": "ok" if ollama_ok else "unavailable",
                "ollama_model": "ok" if ollama_model_ok else "unavailable",
                "qdrant": "ok" if qdrant_ok else "unavailable",
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "Melo-AI",
            "error": str(e)
        }