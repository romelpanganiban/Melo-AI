from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

SETTINGS_FILE = DATA_DIR / "settings.json"
CHAT_HISTORY_FILE = DATA_DIR / "chat_history.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"