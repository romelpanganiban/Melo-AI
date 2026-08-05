from services.settings_manager import SettingsManager


def test_get_settings():

    manager = SettingsManager()

    settings = manager.get_settings()

    assert "model" in settings
    assert "provider" in settings
    assert "temperature" in settings