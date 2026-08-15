from fastapi import APIRouter, status
from pathlib import Path

from core.settings import settings
from core.logging import logger

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
            "status": "healthy" if all_ok else "degraded",
            "service": "Melo-AI",
            "version": "0.1.0",
            "components": {
                "data_directory": "ok" if data_dir_ok else "missing",
                "settings_file": "ok" if settings_file_ok else "missing",
                "sessions_file": "ok" if sessions_file_ok else "missing",
                "chat_history_file": "ok" if history_file_ok else "missing",
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "Melo-AI",
            "error": str(e)
        }