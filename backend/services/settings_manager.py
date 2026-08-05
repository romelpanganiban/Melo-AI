import json
from pathlib import Path


class SettingsManager:

    def __init__(self):
        self.file = Path("data/settings.json")

    def get_settings(self):

        with open(self.file, "r") as f:
            return json.load(f)

    def update_settings(self, settings):

        with open(self.file, "w") as f:
            json.dump(
                settings,
                f,
                indent=4
            )

        return settings