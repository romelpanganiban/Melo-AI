import json
from pathlib import Path


class MemoryManager:

    def __init__(self):
        self.file_path = Path("data/chat_history.json")

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.file_path.exists():
            self.file_path.write_text("[]")

    def load(self):
        with open(self.file_path, "r") as file:
            return json.load(file)

    def save(self, history):
        with open(self.file_path, "w") as file:
            json.dump(history, file, indent=4)

    def add_message(
        self,
        session_id,
        role,
        content
    ):
        history = self.load()

        history.append({
            "session_id": session_id,
            "role": role,
            "content": content
        })

        self.save(history)

    def get_history(self):
        return self.load()

    def get_session_history(
        self,
        session_id
    ):

        history = self.load()

        return [
            message
            for message in history
            if message["session_id"] == session_id
        ]