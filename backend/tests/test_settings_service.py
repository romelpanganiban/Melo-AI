from services.settings_service import SettingsService


def test_get_settings():

    service = SettingsService()

    settings = service.get_settings()

    assert "model" in settings
    assert "provider" in settings
    assert "temperature" in settings