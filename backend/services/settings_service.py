from services.settings_manager import SettingsManager
from core.logging import logger
from core.errors import SettingsError


class SettingsService:
    """Service for handling settings operations"""

    def __init__(self, workspace_id: str = None):
        self.manager = SettingsManager(workspace_id=workspace_id)

    def get_settings(self) -> dict:
        """Get current settings
        
        Returns:
            Dictionary of settings
            
        Raises:
            SettingsError: If operation fails
        """
        try:
            logger.info("Retrieving settings")
            settings = self.manager.get_settings()
            return settings
            
        except Exception as e:
            logger.error(f"Error retrieving settings: {str(e)}")
            raise SettingsError(f"Failed to retrieve settings: {str(e)}")

    def update_settings(self, settings: dict) -> dict:
        """Update settings
        
        Args:
            settings: Dictionary of settings to update
            
        Returns:
            Updated settings
            
        Raises:
            SettingsError: If operation fails
        """
        try:
            logger.info(
                "Updating settings",
                extra={
                    "model": settings.get("model"),
                    "provider": settings.get("provider")
                }
            )
            
            result = self.manager.update_settings(settings)
            return result
            
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            raise SettingsError(f"Failed to update settings: {str(e)}")