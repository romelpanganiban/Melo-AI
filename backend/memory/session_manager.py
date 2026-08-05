import json
from pathlib import Path
from uuid import uuid4


class SessionManager:

    def __init__(self):
        self.file = Path("data/sessions.json")

        self.file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.file.exists():
            self.file.write_text("[]")

    def load(self):
        with open(self.file, "r") as f:
            return json.load(f)

    def save(self, data):
        with open(self.file, "w") as f:
            json.dump(data, f, indent=4)

    def create_session(self):

        sessions = self.load()

        session = {
            "id": str(uuid4()),
            "title": "New Chat"
        }

        sessions.append(session)

        self.save(sessions)

        return session

    def get_sessions(self):
        return self.load()