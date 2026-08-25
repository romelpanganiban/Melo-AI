import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Optional

from core.errors import FileOperationError
from core.logging import logger

_settings_lock = threading.Lock()


class SettingsManager:
    """Manages application settings with file persistence and fallback defaults"""
    
    DEFAULT_SETTINGS = {
        "model": "qwen3:8b",
        "provider": "ollama",
        "temperature": 0.7,
        "context_size": 8192,
        "learning_level": "intermediate",
        "explanation_style": "clear",
        "quiz_difficulty": "medium",
    }

    def __init__(self, file_path: Optional[Path] = None):
        if file_path is None:
            from core.settings import settings
            file_path = settings.SETTINGS_FILE
        
        self.file = Path(file_path)
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Ensure settings file exists, create with defaults if not"""
        try:
            if not self.file.exists():
                logger.info(
                    f"Settings file not found, creating with defaults: {self.file}"
                )
                self.file.parent.mkdir(parents=True, exist_ok=True)
                self.update_settings(self.DEFAULT_SETTINGS)
            else:
                logger.info(f"Settings file found: {self.file}")
        except Exception as e:
            raise FileOperationError(
                f"Failed to ensure settings file: {str(e)}",
                file_path=str(self.file)
            )

    def get_settings(self) -> dict:
        """Get current settings from file
        
        Returns:
            Dictionary of settings
            
        Raises:
            FileOperationError: If file read fails
        """
        try:
            if not self.file.exists():
                logger.warning(
                    f"Settings file missing, returning defaults: {self.file}"
                )
                return self.DEFAULT_SETTINGS.copy()
            
            with open(self.file, "r") as f:
                settings = json.load(f)
                logger.info("Settings loaded successfully")
                return {**self.DEFAULT_SETTINGS, **settings}
                
        except json.JSONDecodeError as e:
            logger.error(
                f"Settings file is invalid JSON: {str(e)}"
            )
            raise FileOperationError(
                f"Settings file is corrupted: {str(e)}",
                file_path=str(self.file)
            )
        except Exception as e:
            logger.error(
                f"Error reading settings file: {str(e)}"
            )
            raise FileOperationError(
                f"Failed to read settings: {str(e)}",
                file_path=str(self.file)
            )

    def update_settings(self, settings: dict) -> dict:
        """Update settings in file
        
        Args:
            settings: Dictionary of settings to save
            
        Returns:
            Updated settings
            
        Raises:
            FileOperationError: If file write fails
        """
        try:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            
            with _settings_lock:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=self.file.parent, delete=False
                ) as temporary:
                    json.dump(settings, temporary, indent=4)
                    temporary.flush()
                    os.fsync(temporary.fileno())
                    temporary_path = temporary.name
                os.replace(temporary_path, self.file)
            
            logger.info("Settings updated successfully")
            return settings
            
        except Exception as e:
            logger.error(
                f"Error writing settings file: {str(e)}"
            )
            raise FileOperationError(
                f"Failed to update settings: {str(e)}",
                file_path=str(self.file)
            )