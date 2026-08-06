from services.settings_manager import SettingsManager
from core.logger import logger


class SettingsService:

    def __init__(self):
        self.manager = SettingsManager()

    def get_settings(self):
        return self.manager.get_settings()

    def update_settings(self, settings):

        logger.info(
            "Settings updated"
        )

        return self.manager.update_settings(
            settings
        )