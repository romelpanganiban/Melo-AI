class MemoryManager:

    def __init__(self):
        self.chat_history = []

    def add_message(self, role, message):
        self.chat_history.append({
            "role": role,
            "message": message
        })

    def get_history(self):
        return self.chat_history
