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

    def rename_session(
        self,
        session_id,
        title
    ):

        sessions = self.load()

        for session in sessions:

            if session["id"] == session_id:

                session["title"] = title

                self.save(sessions)

                return session

        return {
            "message": "Session not found"
        }

    def delete_session(self, session_id):

        sessions = self.load()

        sessions = [
            session
            for session in sessions
            if session["id"] != session_id
        ]

        self.save(sessions)

        return {
            "message": "Session deleted"
        }